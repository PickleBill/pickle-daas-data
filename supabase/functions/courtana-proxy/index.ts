import { serve } from "https://deno.land/std@0.168.0/http/server.ts"

const COURTANA_API = "https://courtana.com/app"

serve(async (req) => {
  const corsHeaders = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  }

  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders })
  }

  const url = new URL(req.url)
  const endpoint = url.searchParams.get("endpoint")

  if (!endpoint) {
    return new Response(JSON.stringify({ error: "endpoint param required" }), {
      status: 400,
      headers: { ...corsHeaders, "Content-Type": "application/json" }
    })
  }

  const courtanaToken = Deno.env.get("COURTANA_TOKEN")
  if (!courtanaToken) {
    return new Response(JSON.stringify({ error: "COURTANA_TOKEN not configured" }), {
      status: 500,
      headers: { ...corsHeaders, "Content-Type": "application/json" }
    })
  }

  try {
    const response = await fetch(`${COURTANA_API}${endpoint}`, {
      headers: { "Authorization": `Bearer ${courtanaToken}` }
    })
    const data = await response.json()
    return new Response(JSON.stringify(data), {
      headers: { ...corsHeaders, "Content-Type": "application/json" }
    })
  } catch (err) {
    return new Response(JSON.stringify({ error: err.message }), {
      status: 502,
      headers: { ...corsHeaders, "Content-Type": "application/json" }
    })
  }
})
