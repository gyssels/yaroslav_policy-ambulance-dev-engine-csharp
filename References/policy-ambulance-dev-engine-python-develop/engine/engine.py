from schema.insight_engine_response import InsightEngineResponse, Insight, Defense, MessageBundle, TranslatedMessage
from schema.insight_engine_request import InsightEngineRequest
from engine.ambulance_policy import ambulance_policy
import uuid

def GetInsights(request: InsightEngineRequest) -> InsightEngineResponse:
    return ambulance_policy(request)
