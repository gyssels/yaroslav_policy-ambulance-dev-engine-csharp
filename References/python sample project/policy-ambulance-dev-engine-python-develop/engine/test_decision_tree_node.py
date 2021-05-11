from engine.tree_node import Predicate
from engine.tree_node import TreeNode
from engine.tree_node import DecisionTreeNode
from engine.tree_node import ResultTreeNode

from schema.insight_engine_response import InsightEngineResponse, Insight, Defense, MessageBundle, TranslatedMessage
from schema.insight_engine_request import InsightEngineRequest
from typing import Callable, TypeVar
import json

A = TypeVar('A')

def test_callable():
    fn: Callable[[str], int] = lambda a: 0
    assert fn("0") == 0

always_true = Predicate[A]("true", lambda request: True)

def test_dtn():
    request = InsightEngineRequest()
    request.id = "id"

    res1 = ResultTreeNode[InsightEngineRequest, str](lambda request: request.id)
    assert res1(request) == "id"
    res2 = ResultTreeNode[InsightEngineRequest, str](lambda request: "res2")
    assert always_true(request)
    dtn = DecisionTreeNode[InsightEngineRequest, str](
        "dtn", 
        always_true,
        res1, 
        res2,
    )
    response = dtn(request)
    assert response == "id"

def ambulance_decision_tree() -> TreeNode[InsightEngineRequest, str]:
    res1 = ResultTreeNode[InsightEngineRequest, str](lambda request: request.claim.id)
    res2 = ResultTreeNode[InsightEngineRequest, str](lambda request: "res2")
    dtn = DecisionTreeNode[InsightEngineRequest, str](
        "dtn", 
        always_true,
        res1, 
        res2,
    )
    return dtn
