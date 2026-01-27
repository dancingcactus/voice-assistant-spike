#!/bin/bash
# Quick demo of Phase 7: Memory & State

echo "🧪 Phase 7 Demo: Memory & State Persistence"
echo "============================================"
echo ""

# Run the automated tests
echo "Running automated tests..."
cd backend && python test_memory.py

echo ""
echo "✅ Tests complete! Now check the persisted data:"
echo ""
echo "View demo user's data:"
echo "  cat data/users/demo_user.json | python -m json.tool"
echo ""
echo "List all user data files:"
echo "  ls -la data/users/"
echo ""
echo "Try the interactive test:"
echo "  python backend/interactive_memory_test.py"
