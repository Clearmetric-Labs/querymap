"""Artifact assembly for querymap."""

from __future__ import annotations

from sqlglot import exp

from .ctes import extract_dependency_edges
from .errors import QueryMapContractError
from .models import QueryMap, QuerySummary, WarningEntry
from .parser import ParsedStatement
from .relations import extract_relations


def build_query_map_from_parsed(parsed: ParsedStatement) -> QueryMap:
    """Build the MVP query map from a parsed statement."""
    relation_extraction = extract_relations(parsed.root_expression, dialect=parsed.dialect)
    dependency_extraction = extract_dependency_edges(
        parsed.root_expression,
        relation_extraction=relation_extraction,
        dialect=parsed.dialect,
    )

    warnings = [
        *dependency_extraction.warnings,
        *_extract_contract_warnings(parsed.root_expression, dialect=parsed.dialect),
    ]

    if not relation_extraction.relations:
        raise QueryMapContractError("No tables or CTE relations were found in the SQL statement.")

    summary = QuerySummary(
        dialect=parsed.dialect,
        statement_type=parsed.statement.key.lower(),
        has_ctes=bool(relation_extraction.cte_relations),
        relation_count=len(relation_extraction.relations),
        cte_count=len(relation_extraction.cte_relations),
        output_count=0,
    )

    return QueryMap(
        summary=summary,
        relations=relation_extraction.relations,
        relation_usages=relation_extraction.relation_usages,
        edges=dependency_extraction.edges,
        outputs=[],
        warnings=_dedupe_warnings(warnings),
    )


def _extract_contract_warnings(
    root_expression: exp.Expression,
    *,
    dialect: str,
) -> list[WarningEntry]:
    warnings: list[WarningEntry] = []

    if root_expression.find(exp.Union) is not None:
        warnings.append(
            WarningEntry(
                code="unsupported_construct",
                message="UNION queries are mapped at the relation level only in the MVP.",
                location=root_expression.find(exp.Union).sql(dialect=dialect),
            )
        )
    if root_expression.find(exp.Intersect) is not None:
        warnings.append(
            WarningEntry(
                code="unsupported_construct",
                message="INTERSECT queries are mapped at the relation level only in the MVP.",
                location=root_expression.find(exp.Intersect).sql(dialect=dialect),
            )
        )
    if root_expression.find(exp.Except) is not None:
        warnings.append(
            WarningEntry(
                code="unsupported_construct",
                message="EXCEPT queries are mapped at the relation level only in the MVP.",
                location=root_expression.find(exp.Except).sql(dialect=dialect),
            )
        )

    for select in root_expression.find_all(exp.Select):
        for selection in select.expressions:
            if isinstance(selection, exp.Star):
                warnings.append(
                    WarningEntry(
                        code="select_star",
                        message="SELECT * was detected; output mapping is deferred in the MVP.",
                        location=selection.sql(dialect=dialect),
                    )
                )
            elif isinstance(selection, exp.Column) and str(selection.name or "").strip() == "*":
                warnings.append(
                    WarningEntry(
                        code="table_star",
                        message="table.* was detected; output mapping is deferred in the MVP.",
                        location=selection.sql(dialect=dialect),
                    )
                )

    for join in root_expression.find_all(exp.Join):
        on_clause = join.args.get("on")
        using_clause = join.args.get("using")
        if on_clause is None and using_clause is None:
            warnings.append(
                WarningEntry(
                    code="unsupported_construct",
                    message="JOIN without ON/USING is not modeled beyond relation dependency mapping.",
                    location=join.sql(dialect=dialect),
                )
            )
            continue
        if on_clause is not None and not _is_equality_join(on_clause):
            warnings.append(
                WarningEntry(
                    code="non_equi_join",
                    message="Non-equality join detected; MVP preserves relation dependencies but does not model join semantics.",
                    location=join.sql(dialect=dialect),
                )
            )

    return warnings


def _is_equality_join(expression: exp.Expression) -> bool:
    if isinstance(expression, exp.EQ):
        return True
    if isinstance(expression, exp.And):
        return _is_equality_join(expression.left) and _is_equality_join(expression.right)
    return False


def _dedupe_warnings(warnings: list[WarningEntry]) -> list[WarningEntry]:
    seen: set[tuple[str, str, str | None]] = set()
    deduped: list[WarningEntry] = []
    for warning in warnings:
        key = (warning.code, warning.message, warning.location)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(warning)
    return deduped
