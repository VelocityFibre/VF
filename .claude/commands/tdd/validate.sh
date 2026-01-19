#!/bin/bash
# /tdd validate
# Validates TDD compliance for the codebase

echo "🔍 TDD Compliance Validation"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

PASS_COUNT=0
FAIL_COUNT=0
WARN_COUNT=0

# Check 1: All specs have corresponding tests
echo "📋 Check 1: Specs have tests"
if [ -d "tests/specs" ]; then
    for spec in tests/specs/*.spec.md; do
        if [ -f "$spec" ]; then
            FEATURE=$(basename "$spec" .spec.md)
            UNIT_TEST="tests/unit/test_${FEATURE}.py"
            INTEGRATION_TEST="tests/integration/test_${FEATURE}_integration.py"

            if [ -f "$UNIT_TEST" ] || [ -f "$INTEGRATION_TEST" ]; then
                echo "  ✅ $FEATURE (has tests)"
                ((PASS_COUNT++))
            else
                echo "  ❌ $FEATURE (no tests found)"
                echo "     Run: /tdd generate $spec"
                ((FAIL_COUNT++))
            fi
        fi
    done
else
    echo "  ⚠️  No specs directory found"
    ((WARN_COUNT++))
fi

echo ""

# Check 2: Test coverage
echo "📊 Check 2: Test coverage"
if [ -f "venv/bin/pytest" ]; then
    COVERAGE=$(./venv/bin/pytest --cov=. --cov-report=term-missing tests/ 2>/dev/null | grep "TOTAL" | awk '{print $NF}' | sed 's/%//')
    if [ ! -z "$COVERAGE" ]; then
        if [ ${COVERAGE%.*} -ge 80 ]; then
            echo "  ✅ Coverage: ${COVERAGE}% (target: 80%)"
            ((PASS_COUNT++))
        else
            echo "  ❌ Coverage: ${COVERAGE}% (below target: 80%)"
            ((FAIL_COUNT++))
        fi
    else
        echo "  ⚠️  Could not calculate coverage"
        ((WARN_COUNT++))
    fi
else
    echo "  ⚠️  pytest not installed (run: pip install pytest pytest-cov)"
    ((WARN_COUNT++))
fi

echo ""

# Check 3: Tests pass
echo "🧪 Check 3: All tests pass"
if [ -f "venv/bin/pytest" ]; then
    if ./venv/bin/pytest tests/ -v --tb=short > /dev/null 2>&1; then
        echo "  ✅ All tests passing"
        ((PASS_COUNT++))
    else
        echo "  ❌ Some tests failing"
        echo "     Run: pytest tests/ -v"
        ((FAIL_COUNT++))
    fi
else
    echo "  ⚠️  pytest not installed"
    ((WARN_COUNT++))
fi

echo ""

# Check 4: No untested code in critical modules
echo "🔬 Check 4: Critical modules have tests"
CRITICAL_MODULES=("workflow" "installations" "projects")
for module in "${CRITICAL_MODULES[@]}"; do
    MODULE_TESTS=$(find tests -name "*${module}*" 2>/dev/null | wc -l)
    if [ $MODULE_TESTS -gt 0 ]; then
        echo "  ✅ ${module} (${MODULE_TESTS} test files)"
        ((PASS_COUNT++))
    else
        echo "  ⚠️  ${module} (no tests found - tightly coupled module!)"
        ((WARN_COUNT++))
    fi
done

echo ""

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Validation Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Passed: $PASS_COUNT"
echo "❌ Failed: $FAIL_COUNT"
echo "⚠️  Warnings: $WARN_COUNT"
echo ""

if [ $FAIL_COUNT -eq 0 ]; then
    echo "🎉 TDD Compliance: PASS"
    echo ""
    echo "✅ Ready to deploy!"
    exit 0
else
    echo "❌ TDD Compliance: FAIL"
    echo ""
    echo "Fix failing checks before deployment."
    exit 1
fi
