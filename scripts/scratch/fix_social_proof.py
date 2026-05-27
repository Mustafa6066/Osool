import re

path = "backend/app/ai_engine/social_proof_engine.py"

with open(path, 'r') as f:
    content = f.read()

# The corrupted _fetch_db_signals body is on one long line with literal \n chars
corrupted_pattern = r'    async def _fetch_db_signals\(self, location: str, db_session\) -> Optional\[Dict\]:\n[^\n]*return None[ ]*\n'

correct_method = (
    '    async def _fetch_db_signals(self, location: str, db_session) -> Optional[Dict]:\n'
    '        """Fetch real-time signals from database using existing tables."""\n'
    '        try:\n'
    '            from sqlalchemy import text\n'
    '\n'
    '            # Count properties in this area as a proxy for activity\n'
    '            props_query = text(\n'
    '                "SELECT COUNT(*) as prop_count "\n'
    '                "FROM properties "\n'
    '                "WHERE location ILIKE :loc AND is_available = true"\n'
    '            )\n'
    '            result = await db_session.execute(props_query, {"loc": f"%{location}%"})\n'
    '            row = result.first()\n'
    '            views = (row[0] if row else 0) * 3  # Estimate views from listing count\n'
    '\n'
    '            # Count recent conversations as a proxy for daily inquiries\n'
    '            conv_query = text(\n'
    '                "SELECT COUNT(*) as conv_count "\n'
    '                "FROM conversations "\n'
    '                "WHERE created_at > NOW() - INTERVAL \'1 day\'"\n'
    '            )\n'
    '            result2 = await db_session.execute(conv_query)\n'
    '            row2 = result2.first()\n'
    '            inquiries = row2[0] if row2 else 0\n'
    '\n'
    '            return {\n'
    '                "views_this_week": views,\n'
    '                "inquiries_today": inquiries,\n'
    '                "recent_deals": [],\n'
    '            }\n'
    '        except Exception as e:\n'
    '            logger.debug(f"DB social query failed (tables may not exist): {e}")\n'
    '            return None\n'
)

match = re.search(corrupted_pattern, content, re.DOTALL)
if match:
    print(f"Found corrupted block ({len(match.group(0))} chars)")
    new_content = content[:match.start()] + correct_method + content[match.end():]
    with open(path, 'w') as f:
        f.write(new_content)
    print("Written. Verifying syntax...")
    import ast
    try:
        ast.parse(new_content)
        print("SYNTAX OK")
    except SyntaxError as e:
        print(f"SYNTAX ERROR at line {e.lineno}: {e.msg}")
else:
    print("Pattern not matched. Lines 170-180:")
    lines = content.splitlines()
    for i, line in enumerate(lines[170:180], start=171):
        print(f"  {i}: {line[:120]!r}")
