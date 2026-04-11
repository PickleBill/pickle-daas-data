#!/usr/bin/env python3
"""
Pickle DaaS — Coach Feedback Loop
===================================
Captures coach ratings on AI analysis outputs. Creates a SQLite database
that the model monitor and prompt evolution tools read to improve prompts.

This is the flywheel: coaches rate AI output → patterns emerge → prompts improve →
better AI output → more trust → more coaches use it.

USAGE:
  # Add feedback
  python tools/feedback-schema.py add --clip 139453f3 --field dupr_estimate \
    --rating 2 --note "Way too low, this player is clearly 4.5+"

  # Add feedback interactively
  python tools/feedback-schema.py add --clip 139453f3 --interactive

  # List recent feedback
  python tools/feedback-schema.py list

  # Show summary report (feeds into prompt evolution)
  python tools/feedback-schema.py report

  # Seed with example records (for demo purposes)
  python tools/feedback-schema.py seed

DB: output/coaching-feedback.db (SQLite, zero deps, Supabase-ready schema)
"""

import os
import sys
import json
import sqlite3
import argparse
import glob
from datetime import datetime
from pathlib import Path

DB_PATH = 'output/coaching-feedback.db'

# Ratable fields — what coaches can rate
RATABLE_FIELDS = {
    'dupr_estimate':          'DUPR Rating Estimate',
    'signature_move':         'Signature Move Detection',
    'coaching_breakdown':     'Coaching Breakdown Quality',
    'improvement_opportunities': 'Improvement Opportunities',
    'skill_ratings':          'Skill Ratings (overall)',
    'badge_predictions':      'Badge Predictions',
    'shot_analysis':          'Shot Analysis',
    'brand_detection':        'Brand Detection',
    'overall_accuracy':       'Overall Clip Accuracy',
}

RATING_LABELS = {
    1: '❌ Way off',
    2: '⚠️  Off / partially wrong',
    3: '→ Acceptable',
    4: '✅ Good',
    5: '⭐ Spot on / impressive',
}

SEED_RECORDS = [
    {
        'clip_id':    '139453f3',
        'field_name': 'dupr_estimate',
        'ai_value':   '3.5-4.0',
        'coach_rating': 4,
        'coach_note': 'Seems right for this player. Good kitchen fundamentals visible.',
        'coach_name': 'Demo Coach',
    },
    {
        'clip_id':    '139453f3',
        'field_name': 'coaching_breakdown',
        'ai_value':   'Excellent patience in the dink exchange, maintaining low balls. Player 2 recognized the slight opening, stepped in, and drove through the ball with conviction.',
        'coach_rating': 5,
        'coach_note':   'This is accurate and well-observed. The transition timing is exactly right.',
        'coach_name':   'Demo Coach',
    },
    {
        'clip_id':    '08932731',
        'field_name': 'dupr_estimate',
        'ai_value':   '3.0-3.5',
        'coach_rating': 2,
        'coach_note': 'Too low. The footwork and kitchen positioning suggest at least 3.5-4.0.',
        'coach_name': 'Demo Coach',
    },
    {
        'clip_id':    '42520eda',
        'field_name': 'badge_predictions',
        'ai_value':   'Kitchen King, Epic Rally',
        'coach_rating': 3,
        'coach_note': 'Kitchen King makes sense but Epic Rally is a stretch for a 6-shot point.',
        'coach_name': 'Demo Coach',
    },
    {
        'clip_id':    '6ee49439',
        'field_name': 'shot_analysis',
        'ai_value':   'dominant_shot_type: dink',
        'coach_rating': 4,
        'coach_note': 'Correct. Heavy dink-based rally with one speed-up.',
        'coach_name': 'Demo Coach',
    },
    {
        'clip_id':    'f4df1bb4',
        'field_name': 'signature_move',
        'ai_value':   None,
        'coach_rating': 1,
        'coach_note': 'This was null — the player clearly has an explosive forehand speed-up they use repeatedly.',
        'coach_name': 'Demo Coach',
    },
    {
        'clip_id':    'eb168c8c',
        'field_name': 'skill_ratings',
        'ai_value':   'kitchen_mastery: 3, court_iq: 4',
        'coach_rating': 3,
        'coach_note': 'Kitchen mastery feels low. Player showed good patience but AI scored them a 3.',
        'coach_name': 'Demo Coach',
    },
]


def get_db():
    """Get or create the feedback database."""
    os.makedirs('output', exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    conn.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            clip_id       TEXT NOT NULL,
            field_name    TEXT NOT NULL,
            ai_value      TEXT,
            coach_rating  INTEGER NOT NULL CHECK(coach_rating BETWEEN 1 AND 5),
            coach_note    TEXT,
            coach_name    TEXT DEFAULT 'anonymous',
            session_id    TEXT,
            created_at    TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)

    # Aggregated view for quick reporting
    conn.execute("""
        CREATE VIEW IF NOT EXISTS feedback_summary AS
        SELECT
            field_name,
            COUNT(*) as rating_count,
            ROUND(AVG(coach_rating), 2) as avg_rating,
            SUM(CASE WHEN coach_rating <= 2 THEN 1 ELSE 0 END) as low_count,
            SUM(CASE WHEN coach_rating >= 4 THEN 1 ELSE 0 END) as high_count,
            MIN(coach_rating) as min_rating,
            MAX(coach_rating) as max_rating
        FROM feedback
        GROUP BY field_name
        ORDER BY avg_rating ASC
    """)

    conn.commit()
    return conn


def cmd_add(args):
    """Add a single feedback record."""
    conn = get_db()

    clip_id    = args.clip
    field_name = args.field
    rating     = args.rating
    note       = args.note or ''
    coach_name = args.coach or 'anonymous'
    ai_value   = args.ai_value or ''

    if args.interactive:
        print(f"\nAdding feedback for clip: {clip_id}")
        print("\nAvailable fields:")
        for k, v in RATABLE_FIELDS.items():
            print(f"  {k:35} {v}")
        field_name = input("\nField to rate: ").strip()
        if field_name not in RATABLE_FIELDS:
            print(f"Unknown field. Valid: {', '.join(RATABLE_FIELDS.keys())}")
            sys.exit(1)

        print("\nRatings:")
        for k, v in RATING_LABELS.items():
            print(f"  {k} = {v}")
        rating = int(input("Rating (1-5): ").strip())
        note = input("Note (optional): ").strip()
        ai_value = input("AI's actual value (optional, for reference): ").strip()

    if not field_name:
        print("❌ --field is required")
        sys.exit(1)
    if not rating or not (1 <= rating <= 5):
        print("❌ --rating must be 1-5")
        sys.exit(1)

    conn.execute(
        "INSERT INTO feedback (clip_id, field_name, ai_value, coach_rating, coach_note, coach_name) VALUES (?,?,?,?,?,?)",
        (clip_id, field_name, ai_value, rating, note, coach_name)
    )
    conn.commit()

    label = RATABLE_LABELS = RATABLE_FIELDS.get(field_name, field_name)
    rating_label = RATING_LABELS.get(rating, str(rating))
    print(f"\n✅ Feedback saved")
    print(f"   Clip:   {clip_id}")
    print(f"   Field:  {label}")
    print(f"   Rating: {rating_label}")
    if note:
        print(f"   Note:   {note}")

    conn.close()


def cmd_list(args):
    """List recent feedback records."""
    conn = get_db()
    limit = getattr(args, 'limit', 20)
    rows = conn.execute(
        "SELECT * FROM feedback ORDER BY created_at DESC LIMIT ?", (limit,)
    ).fetchall()

    if not rows:
        print("No feedback records yet. Run: python tools/feedback-schema.py seed")
        conn.close()
        return

    print(f"\n{'ID':>4}  {'Clip':10} {'Field':30} {'Rating':8} Note")
    print("-" * 80)
    for r in rows:
        rating_icon = {1:'❌',2:'⚠️ ',3:'→ ',4:'✅',5:'⭐'}.get(r['coach_rating'],'  ')
        note = (r['coach_note'] or '')[:40]
        print(f"{r['id']:>4}  {r['clip_id'][:10]:10} {r['field_name'][:30]:30} {rating_icon} {r['coach_rating']}    {note}")

    print(f"\nTotal: {len(rows)} records shown")
    conn.close()


def cmd_report(args):
    """Generate a prompt improvement report from feedback data."""
    conn = get_db()

    summary_rows = conn.execute("SELECT * FROM feedback_summary").fetchall()
    all_low = conn.execute(
        "SELECT clip_id, field_name, ai_value, coach_rating, coach_note FROM feedback WHERE coach_rating <= 2 ORDER BY coach_rating ASC"
    ).fetchall()

    if not summary_rows:
        print("No feedback yet. Add feedback first or run: python tools/feedback-schema.py seed")
        conn.close()
        return

    print("\n📊 Feedback Report — Prompt Improvement Guide")
    print("=" * 60)

    print("\n## Field Accuracy Scores (avg coach rating / 5.0)")
    print(f"{'Field':35} {'Avg':>5} {'Count':>6} {'Low':>5} {'High':>5}")
    print("-" * 60)
    for r in summary_rows:
        label = RATABLE_FIELDS.get(r['field_name'], r['field_name'])
        bar = '█' * int(r['avg_rating']) + '░' * (5 - int(r['avg_rating']))
        flag = " ← FIX THIS" if r['avg_rating'] < 3.0 else (" ← monitor" if r['avg_rating'] < 3.5 else "")
        print(f"{label[:35]:35} {r['avg_rating']:>5.1f} {r['rating_count']:>6} {r['low_count']:>5} {r['high_count']:>5}{flag}")

    if all_low:
        print("\n## Low-Rating Records (coach said AI was wrong)")
        print(f"{'Clip':10} {'Field':30} {'AI Value':25} Note")
        print("-" * 80)
        for r in all_low:
            ai_val = (str(r['ai_value'] or 'null'))[:22]
            note = (r['coach_note'] or '')[:35]
            print(f"{r['clip_id'][:10]:10} {r['field_name'][:30]:30} {ai_val:25} {note}")

    # Generate prompt update recommendations
    low_fields = [r for r in summary_rows if r['avg_rating'] < 3.0]
    if low_fields:
        print("\n## Recommended Prompt Updates")
        for r in low_fields:
            label = RATABLE_FIELDS.get(r['field_name'], r['field_name'])
            print(f"\n  Field: {label}")
            print(f"  Issue: avg rating {r['avg_rating']:.1f}/5 across {r['rating_count']} coach ratings")

            # Get example notes for this field
            notes = conn.execute(
                "SELECT coach_note FROM feedback WHERE field_name=? AND coach_rating<=2 AND coach_note != '' LIMIT 3",
                (r['field_name'],)
            ).fetchall()
            for n in notes:
                print(f"  Coach: \"{n['coach_note']}\"")
            print(f"  Action: Add few-shot examples + clarifying instructions for '{r['field_name']}' in prompt")

    # Write to markdown
    output_path = 'output/feedback-report.md'
    with open(output_path, 'w') as f:
        f.write(f"# Coach Feedback Report\n**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
        f.write("## Field Accuracy (avg coach rating / 5.0)\n\n")
        f.write("| Field | Avg Rating | Ratings | Low | High | Action |\n")
        f.write("|---|---|---|---|---|---|\n")
        for r in summary_rows:
            label = RATABLE_FIELDS.get(r['field_name'], r['field_name'])
            action = "🔴 Fix prompt" if r['avg_rating'] < 3.0 else ("🟡 Monitor" if r['avg_rating'] < 3.5 else "🟢 Good")
            f.write(f"| {label} | {r['avg_rating']:.1f} | {r['rating_count']} | {r['low_count']} | {r['high_count']} | {action} |\n")
        if all_low:
            f.write("\n## Coach Corrections (Rating ≤ 2)\n\n")
            for r in all_low:
                f.write(f"- **{r['clip_id']}** / `{r['field_name']}`: AI said `{r['ai_value']}` — Coach: \"{r['coach_note']}\"\n")

    print(f"\n✅ Report saved: {output_path}")
    conn.close()


def cmd_seed(args):
    """Seed the database with example feedback records."""
    conn = get_db()
    count = 0
    for record in SEED_RECORDS:
        try:
            conn.execute(
                "INSERT INTO feedback (clip_id, field_name, ai_value, coach_rating, coach_note, coach_name) VALUES (?,?,?,?,?,?)",
                (record['clip_id'], record['field_name'],
                 json.dumps(record['ai_value']) if not isinstance(record['ai_value'], str) else record['ai_value'],
                 record['coach_rating'], record['coach_note'], record['coach_name'])
            )
            count += 1
        except Exception as e:
            print(f"  Skip: {e}")
    conn.commit()
    print(f"✅ Seeded {count} example feedback records into {DB_PATH}")
    conn.close()

    # Show the report immediately
    class FakeArgs:
        pass
    cmd_report(FakeArgs())


def main():
    parser = argparse.ArgumentParser(description='Coach feedback loop for Pickle DaaS model improvement')
    sub = parser.add_subparsers(dest='command')

    # add
    p_add = sub.add_parser('add', help='Add a feedback record')
    p_add.add_argument('--clip',        required=True, help='Clip ID (short prefix, e.g. 139453f3)')
    p_add.add_argument('--field',       default=None,  help='Field to rate (e.g. dupr_estimate)')
    p_add.add_argument('--rating',      type=int,      help='1-5 rating')
    p_add.add_argument('--note',        default='',    help='Coach note / correction')
    p_add.add_argument('--coach',       default='anonymous', help='Coach name')
    p_add.add_argument('--ai-value',    default='',    help='AI output value being rated')
    p_add.add_argument('--interactive', action='store_true', help='Interactive mode')

    # list
    p_list = sub.add_parser('list', help='List recent feedback')
    p_list.add_argument('--limit', type=int, default=20)

    # report
    sub.add_parser('report', help='Generate prompt improvement report')

    # seed
    sub.add_parser('seed', help='Seed with example records (demo)')

    args = parser.parse_args()

    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    if args.command == 'add':
        cmd_add(args)
    elif args.command == 'list':
        cmd_list(args)
    elif args.command == 'report':
        cmd_report(args)
    elif args.command == 'seed':
        cmd_seed(args)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
