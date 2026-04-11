-- =============================================================================
-- PICKLE DaaS — Supabase Seed Data
-- Run AFTER supabase-schema.sql.
-- Uses realistic placeholder data modeled after real Courtana/PickleBill data.
-- =============================================================================

-- ---------------------------------------------------------------------------
-- Sample analysis row (PickleBill highlight)
-- ---------------------------------------------------------------------------
INSERT INTO pickle_daas_analyses (
  highlight_id, highlight_name, video_url,
  clip_quality_score, viral_potential_score, watchability_score, cinematic_score,
  brands_detected, predicted_badges, play_style_tags,
  commentary_espn, commentary_hype, commentary_social_caption,
  commentary_ron_burgundy, commentary_tts_clean,
  clip_summary, search_tags, story_arc, highlight_category,
  full_analysis, batch_id, clip_rank_in_batch
) VALUES (
  'KyRtzDmrpBQN',
  'Epic Rally #427',
  'https://cdn.courtana.com/files/production/u/01915c59-9bb7-4683-bd53-e28bddcae12e/ce00696b-9f9b-465a-971c-dbf1334e556c.mp4',
  8.4,
  7.9,
  8.1,
  7.2,
  '[{"brand_name":"Selkirk","category":"paddle","confidence":"high","player_side":"right","visibility_quality":"clear","estimated_visible_seconds":12,"color_scheme_noted":"black and red"},{"brand_name":"JOOLA","category":"apparel_top","confidence":"medium","player_side":"left","visibility_quality":"partial","estimated_visible_seconds":8,"color_scheme_noted":"blue and white"}]',
  '[{"badge_name":"Epic Rally","confidence":"high","reasoning":"23-shot rally with multiple erne attempts and kitchen resets"},{"badge_name":"Kitchen King","confidence":"high","reasoning":"Player maintained dominant kitchen position for 80% of the clip"}]',
  '["kitchen specialist","net rusher","touch player","counter_puncher"]',
  'An extraordinary 23-shot kitchen battle unfolds as PickleBill methodically dismantles his opponent with precision dinks and a perfectly-timed erne attempt. The crowd erupts as the point is sealed with a cross-court winner.',
  'NOBODY STOPS THE BILL TRAIN! Twenty-three shots of pure pickleball MASTERY! That erne attempt had the crowd LOSING THEIR MINDS!',
  'This kitchen rally just broke physics 🔥🥒 #pickleball',
  'By the beard of Zeus, that was a pickleball clinic! PickleBill commanded that kitchen like a seasoned diplomat at a very competitive lunch meeting. Stay classy, The Underground.',
  'PickleBill executes a 23-shot kitchen rally, finishing with a cross-court erne winner at The Underground.',
  'PickleBill wins a 23-shot kitchen battle with an erne at The Underground',
  '["erne","kitchen rally","dink","pickleball","competitive","long rally","erne attempt","cross-court","winner","net play","kitchen specialist","23 shots","highlight reel","indoor court","doubles"]',
  'clutch_moment',
  'top_play',
  '{"analyzed_at":"2026-03-28T00:00:00Z","model_used":"gemini-2.5-flash","clip_meta":{"duration_seconds":34,"clip_quality_score":8.4,"viral_potential_score":7.9,"watchability_score":8.1,"cinematic_score":7.2},"daas_signals":{"data_richness_score":9,"match_context_inferred":"competitive","estimated_player_rating_dupr":"4.5-5.0"}}',
  'seed-data',
  1
);

-- ---------------------------------------------------------------------------
-- Sample brand rows
-- ---------------------------------------------------------------------------
INSERT INTO pickle_daas_brands (brand_name, category, total_appearances, total_clips_seen_in, player_usernames, avg_confidence, last_seen_at)
VALUES
  ('Selkirk',  'paddle',       14, 11, '["PickleBill","Chintan","Coach_Block"]', 'high',   now()),
  ('JOOLA',    'paddle',        9,  7, '["PickleBill","tshell"]',                'medium', now()),
  ('Engage',   'paddle',        6,  5, '["Coach_Block","Chintan"]',              'high',   now()),
  ('HEAD',     'paddle',        4,  4, '["tshell"]',                             'medium', now()),
  ('Nike',     'apparel_top',  11,  9, '["PickleBill","Chintan","tshell"]',      'high',   now()),
  ('Adidas',   'shoes',         7,  6, '["PickleBill","Coach_Block"]',           'medium', now()),
  ('Franklin', 'ball',          8,  8, '["PickleBill","Chintan","tshell","Coach_Block"]', 'high', now())
ON CONFLICT (brand_name, category) DO UPDATE
  SET total_appearances = EXCLUDED.total_appearances,
      last_seen_at      = EXCLUDED.last_seen_at;

-- ---------------------------------------------------------------------------
-- PickleBill player DNA row
-- ---------------------------------------------------------------------------
INSERT INTO pickle_daas_player_dna (
  player_username, clips_analyzed, avg_quality_score, avg_viral_score,
  dominant_shot_type, play_style_tags, skill_aggregate, brands_worn, top_badges,
  top_clips, coaching_notes
) VALUES (
  'PickleBill',
  20,
  7.8,
  7.2,
  'dink',
  '["kitchen specialist","net rusher","touch player","counter_puncher","lefty banger"]',
  '{"court_coverage_rating":8.1,"kitchen_mastery_rating":9.2,"power_game_rating":6.4,"touch_and_feel_rating":8.8,"athleticism_rating":7.9,"creativity_rating":8.5,"court_iq_rating":8.9,"consistency_rating":8.2,"composure_under_pressure":8.6}',
  '[{"brand_name":"Selkirk","category":"paddle","count":14},{"brand_name":"Adidas","category":"shoes","count":7},{"brand_name":"Nike","category":"apparel_top","count":5}]',
  '[{"badge_name":"Epic Rally","count":38,"confidence":"high"},{"badge_name":"Kitchen King","count":22,"confidence":"high"},{"badge_name":"Highlight Reel","count":17,"confidence":"high"}]',
  '[{"highlight_id":"KyRtzDmrpBQN","name":"Epic Rally #427","quality_score":8.4,"video_url":"https://cdn.courtana.com/files/production/u/01915c59-9bb7-4683-bd53-e28bddcae12e/ce00696b-9f9b-465a-971c-dbf1334e556c.mp4","caption":"This kitchen rally just broke physics"}]',
  '["Work on power game — drives score 6.4 vs kitchen 9.2","Improve transition zone patience — tends to rush the kitchen","Expand shot variety: more speed-ups to break dink patterns"]'
)
ON CONFLICT (player_username) DO UPDATE
  SET clips_analyzed    = EXCLUDED.clips_analyzed,
      avg_quality_score = EXCLUDED.avg_quality_score,
      last_updated      = now();
