from __future__ import annotations

import pytest
from clearmetric.cleaner import enforce_checks
from clearmetric.core.errors import StructuralCheckError
from clearmetric.core.interop import attach_warehouse_bindings
from clearmetric.core.models import (
    CatalogArtifact,
    DerivationState,
    Node,
    PhysicalBinding,
)


def _warehouse_table(name: str, *, warehouse: str = "jaffle") -> Node:
    binding = PhysicalBinding(warehouse=warehouse, schema="analytics", table=name)
    return Node(
        id=f"table:analytics.{name}",
        kind="table",
        name=name,
        qualified_name=f"analytics.{name}",
        derivation=DerivationState(
            status="complete", confidence="high", source="information_schema"
        ),
        bindings=[binding],
    )


def _warehouse_column(table: str, column: str, *, warehouse: str = "jaffle") -> Node:
    binding = PhysicalBinding(
        warehouse=warehouse,
        schema="analytics",
        table=table,
        column=column,
    )
    return Node(
        id=f"column:analytics.{table}.{column}",
        kind="column",
        name=column,
        qualified_name=f"analytics.{table}.{column}",
        derivation=DerivationState(
            status="complete", confidence="high", source="information_schema"
        ),
        bindings=[binding],
    )


def test_alias_resolves_mismatched_table_binding():
    warehouse = CatalogArtifact(
        nodes=[_warehouse_table("orders"), _warehouse_column("orders", "amount")]
    )
    merged = CatalogArtifact(
        nodes=[
            Node(
                id="table:orders",
                kind="table",
                name="orders",
                qualified_name="orders",
                derivation=DerivationState(
                    status="complete", confidence="high", source="dbt_manifest"
                ),
            ),
            Node(
                id="column:orders.amount",
                kind="column",
                name="amount",
                qualified_name="orders.amount",
                derivation=DerivationState(
                    status="complete", confidence="high", source="dbt_manifest"
                ),
            ),
        ]
    )
    result = attach_warehouse_bindings(
        merged=merged,
        warehouse_artifact=warehouse,
        alias_map={"orders": "analytics.orders"},
    )
    table = next(node for node in result.nodes if node.id == "table:orders")
    column = next(node for node in result.nodes if node.id == "column:orders.amount")
    assert table.bindings
    assert column.bindings
    assert table.bindings[0].table == "orders"
    assert column.bindings[0].column == "amount"


def test_unresolved_emits_warning_without_binding():
    warehouse = CatalogArtifact(nodes=[_warehouse_table("customers")])
    merged = CatalogArtifact(
        nodes=[
            Node(
                id="table:orders",
                kind="table",
                name="orders",
                qualified_name="orders",
                derivation=DerivationState(
                    status="complete", confidence="high", source="dbt_manifest"
                ),
            )
        ]
    )
    result = attach_warehouse_bindings(
        merged=merged,
        warehouse_artifact=warehouse,
        alias_map=None,
    )
    table = next(node for node in result.nodes if node.id == "table:orders")
    assert not table.bindings
    assert any(w.code == "warehouse_bind_unresolved" for w in result.warnings)


def test_duplicate_bindings_fail_enforce():
    binding = PhysicalBinding(
        warehouse="jaffle",
        schema="analytics",
        table="orders",
        column="amount",
    )
    artifact = CatalogArtifact(
        nodes=[
            Node(
                id="column:a",
                kind="column",
                name="amount",
                qualified_name="a.amount",
                bindings=[binding],
            ),
            Node(
                id="column:b",
                kind="column",
                name="amount",
                qualified_name="b.amount",
                bindings=[binding],
            ),
        ]
    )
    with pytest.raises(StructuralCheckError, match="duplicate_bindings"):
        enforce_checks(artifact, posture="strict")
