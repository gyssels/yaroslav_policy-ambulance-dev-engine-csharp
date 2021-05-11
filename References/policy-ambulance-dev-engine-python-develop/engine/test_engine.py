from fhir.resources.claim import Claim, ClaimItem, ClaimInsurance
from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.coding import Coding
from fhir.resources.period import Period
from fhir.resources.address import Address
from fhir.resources.organization import Organization

from schema.insight_engine_response import InsightEngineResponse, Insight, Defense, MessageBundle, TranslatedMessage
from schema.insight_engine_request import InsightEngineRequest
from engine.engine import GetInsights
import json

def test_GetInsights():
    request = InsightEngineRequest()
    claim1 = readClaim1()
    request.claim = claim1
    response = GetInsights(request)
    insight = response.insights[0]
    assert insight.id == claim1.id
    # Claim Not Payable, 
    assert insight.defense.script.messages[0].message == "TMHP does not reimburse ambulance claims if a valid transport code is not present on the claim (if a client has not been transported)"

def readClaim1() -> Claim:
    claim1 = Claim.parse_file("engine/claim1.json")
    return claim1
    
def test_claim1():
    claim1 = readClaim1()
    assert claim1.id == "claim1234"
    assert claim1.item[0].productOrService.coding[0].code == "0028U"
    assert claim1.type.id == "something"
