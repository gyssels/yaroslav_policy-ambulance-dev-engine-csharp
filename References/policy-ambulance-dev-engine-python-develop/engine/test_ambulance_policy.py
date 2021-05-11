from typing import List
from engine.tree_node import TreeNode

from schema.insight_engine_request import InsightEngineRequest

from typing import Callable
from engine.ambulance_policy import ambulance_decision_claim_tree, ambulance_decision_claim_line_tree
from engine.ambulance_policy import claimLines, ClaimLineFocus
import json
import pytest # type: ignore
import typing
from importlib import resources
from schema.insight_engine_response import InsightType
from engine.simple_insight import SimpleInsight

import engine.TestInputs

def readRequest(filename: str) -> InsightEngineRequest:
    text = resources.read_text(engine.TestInputs, filename)
    requestJson = json.loads(text)
    request = InsightEngineRequest(**requestJson)
    return request

class ClaimCase():
    def __init__(self, filename, expected_insight_type: InsightType, expected_text: str):
        self.filename = filename
        self.expected_insight_type = expected_insight_type
        self.expected_text = expected_text

    def testTree(self, tree: TreeNode[InsightEngineRequest, SimpleInsight]):
        request = readRequest(self.filename)
        response = tree(request)
        assert response.insight_type == self.expected_insight_type, "For file " + self.filename
        assert response.text == self.expected_text, "For file " + self.filename

claim_cases: List[ClaimCase] = [
    # Case("TestNode100_No.json", "Not Applicable, this policy is specific for TMHP Ambulance Claims submitted on the CMS-1500 paper claim form")
    ClaimCase("TestNode200_No.json", InsightType.ClaimNotPayable, "TMHP does not reimburse ambulance claims if a valid transport code is not present on the claim (if a client has not been transported)"),
    ClaimCase("TestNode300_No.json", InsightType.ClaimNotPayable, "TMHP does not reimburse ambulance claims if a valid origin-destination modifier is not present on every claim line"),
]

claim_tree = ambulance_decision_claim_tree()

@pytest.mark.parametrize("case", claim_cases, ids = [case.filename for case in claim_cases])
def test_claim_case(case: ClaimCase):
    case.testTree(claim_tree)

class ClaimLineCase():
    def __init__(self, filename, expected_insight_type: InsightType, expected_text: str):
        self.filename = filename
        self.expected_insight = SimpleInsight(expected_insight_type, expected_text)

    def testTree(self, tree: TreeNode[ClaimLineFocus, SimpleInsight]):
        request = readRequest(self.filename)
        insights = [tree(ClaimLineFocus(cl, request)) for cl in claimLines(request)]
        assert self.expected_insight in insights, "For file " + self.filename

claim_line_cases: List[ClaimLineCase] = [
    # ClaimLineCase("TestNode300_No.json", "TODO"),
    ClaimLineCase("TestNode400_No.json",   InsightType.ClaimNotPayable, "Invalid Place of Service for claim type CMS-1500 (paper claim)"),
    ClaimLineCase("TestNode500_Yes.json",  InsightType.ClaimLineNotPayable, "Cardiopulmonary Resuscitation (CPR) is not separately payable and is included in ambulance transport fees"),
    ClaimLineCase("TestNode700_Yes.json",  InsightType.ClaimLineNotPayable, "Disposable Supplies are not Separately Payable when used during Specialty Care Transport"),
    ClaimLineCase("TestNode900_No.json",   InsightType.ClaimLineNotPayable, "TMHP does not reimburse for disposable supplies when a transport did not occur for the same trip (matching dates and modifiers)"),
    ClaimLineCase("TestNode1000_No.json",  InsightType.ClaimLineNotPayable, "TMHP does not reimburse for oxygen supplies when a transport did not occur for the same trip (matching dates and modifiers)"),
    ClaimLineCase("TestNode1200_No.json",  InsightType.ClaimLineValid, "Disposable Supply is payable."),
    ClaimLineCase("TestNode1200_Yes.json", InsightType.RecodeClaimLine, "Change Units to 1. Disposable Supplies are only reimbursed once per trip for air or ground transport"),
    ClaimLineCase("TestNode1300_No.json",  InsightType.ClaimLineValid, "Oxygen Supply is payable."),
    ClaimLineCase("TestNode1300_Yes.json", InsightType.RecodeClaimLine, "Change Units to 1. Oxygen Supplies are only reimbursed once per trip for air or ground transport"),
    ClaimLineCase("TestNode1600_No.json",  InsightType.ClaimLineNotPayable, "TMHP does not reimburse for extra attendant when a transport did not occur for the same trip"),
    ClaimLineCase("TestNode1600_Yes.json", InsightType.ClaimLineValid, "Extra Attendant is payable."),
    ClaimLineCase("TestNode1700_Yes.json", InsightType.ClaimNotPayable, "If emergency transport is being claimed, then all claimed lines for the same trip must include the modifier ET."),
    ClaimLineCase("TestNode1725_No.json",  InsightType.ClaimLineNotPayable, "TMHP does not reimburse for an extra attendant without a corresponding Transport for the same trip"),
    ClaimLineCase("TestNode1800_No.json",  InsightType.ClaimNotPayable, "Emergency transport must include an approved ICD-10-CM code. Appeal required to prove emergency transport was provided."),
    ClaimLineCase("TestNode1900_Yes.json", InsightType.ClaimNotPayable, "If emergency transport is being claimed, then all claimed lines for the same trip must include the modifier ET."),
    ClaimLineCase("TestNode2000_No-Fixed.json",  InsightType.ClaimNotPayable, "TMHP does not reimburse for a non-emergency extra attendant without a prior authorization on file"),
    ClaimLineCase("TestNode2000_Yes-Fixed.json", InsightType.ClaimLineValid, "Extra Attendant is payable."),
    ClaimLineCase("TestNode2200_No.json",  InsightType.ClaimNotPayable, "If emergency transport is being claimed, then all claimed lines for the same trip must include the modifier ET."),
    ClaimLineCase("TestNode2300_No.json",  InsightType.ClaimNotPayable, "Emergency transport code must be submitted with a corresponding mileage code for same trip (matching dates and modifiers)."),
    ClaimLineCase("TestNode2600_No.json",  InsightType.ClaimNotPayable, "Emergency transport code must be submitted with a corresponding mileage code with units greater than 0"),
    ClaimLineCase("TestNode2600_Yes.json", InsightType.ClaimLineValid, "Emergency Ground Transport is payable"),
    ClaimLineCase("TestNode2800_No.json",  InsightType.ClaimNotPayable, "Emergency transport code must be submitted with a corresponding mileage code for same trip (matching dates and modifiers)."),
    ClaimLineCase("TestNode3000_No.json",  InsightType.ClaimNotPayable, "Emergency transport code must be submitted with a corresponding mileage code for same trip (matching dates and modifiers)."),
    ClaimLineCase("TestNode3100_No.json", InsightType.ClaimNotPayable, "Emergency transport code must be submitted with a corresponding mileage code for same trip (matching dates and modifiers)."),
    ClaimLineCase("TestNode3200_No.json", InsightType.ClaimNotPayable, "Emergency transport code must be submitted with a corresponding mileage code with units greater than 0"),
    ClaimLineCase("TestNode3200_Yes.json", InsightType.ClaimLineValid, "Emergency Ground Transport is payable"),
    ClaimLineCase("TestNode3400_No.json", InsightType.ClaimNotPayable, "Emergency transport code must be submitted with a corresponding mileage code with units greater than 0"),
    ClaimLineCase("TestNode3400_Yes.json", InsightType.ClaimLineValid, "Emergency Rotary Wing Air Transport is payable"),
    ClaimLineCase("TestNode3500_No.json", InsightType.ClaimNotPayable, "Emergency transport code must be submitted with a corresponding mileage code with units greater than 0"),
    ClaimLineCase("TestNode3500_Yes.json", InsightType.ClaimLineValid, "Emergency Fixed Wing Air Transport is payable"),
    ClaimLineCase("TestNode3600_No.json", InsightType.ClaimNotPayable, "Non-Emergency transport code must be submitted with a corresponding mileage code for same trip (matching dates and modifiers)."),
    ClaimLineCase("TestNode3700_No.json", InsightType.ClaimNotPayable, "Non-Emergency transport code must be submitted with a corresponding mileage code for same trip (matching dates and modifiers)."),
    ClaimLineCase("TestNode3800_No.json", InsightType.ClaimNotPayable, "Non-Emergency transport code must be submitted with a corresponding mileage code with units greater than 0"),
    ClaimLineCase("TestNode3800_Yes.json", InsightType.ClaimLineValid, "Non-Emergency Rotary Wing Air Transport is payable"),
    ClaimLineCase("TestNode3900_No.json", InsightType.ClaimNotPayable, "Non-Emergency transport code must be submitted with a corresponding mileage code with units greater than 0"),
    ClaimLineCase("TestNode3900_Yes.json", InsightType.ClaimLineValid, "Non-Emergency Fixed Wing Air Transport is payable"),
    ClaimLineCase("TestNode4100_No.json", InsightType.ClaimNotPayable, "Air Transport Mileage for Fixed Wing Air Transport requires the billing for Fixed Wing Air Transport A0431"),
    ClaimLineCase("TestNode4300_No.json", InsightType.ClaimNotPayable, "Mileage code with units greater than 0 must be submitted with corresponding Emergency transport code."),
    ClaimLineCase("TestNode4300_Yes.json", InsightType.ClaimLineValid, "Mileage for Emergency Fixed Wing Air Transport is payable"),
    ClaimLineCase("TestNode4400_No.json", InsightType.ClaimNotPayable, "Air Transport Mileage for Rotary Wing Air Transport requires the billing for Rotary Wing Air Transport A0430"),
    ClaimLineCase("TestNode4600_No.json", InsightType.ClaimNotPayable, "Emergency rotary wing air mileage code must be submitted  with units greater than 0"),
    ClaimLineCase("TestNode4600_Yes.json", InsightType.ClaimLineValid, "Emergency Rotary Wing Air Transport is payable"),
    ClaimLineCase("TestNode4700_No.json", InsightType.ClaimNotPayable, "Ground Transport Mileage must be submitted with a corresponding Ground Transport code"),
    ClaimLineCase("TestNode4800_No.json", InsightType.ClaimNotPayable, "Emergency ground mileage code must be submitted with units greater than 0"),
    ClaimLineCase("TestNode4800_Yes.json", InsightType.ClaimLineValid, "Emergency Ground Transport is payable"),
    ClaimLineCase("TestNode5000_No.json", InsightType.ClaimNotPayable, "Fixed Wing Air Transport Mileage for Fixed Wing Air Transport requires the billing for Fixed Wing Air Transport code A0430"),
    ClaimLineCase("TestNode5200_No.json", InsightType.ClaimNotPayable, "Non-Emergency transport code must be submitted with a corresponding mileage code with units greater than 0"),
    ClaimLineCase("TestNode5200_Yes.json", InsightType.ClaimLineValid, "Non-Emergency Fixed Wing Air Transport is payable"),
    ClaimLineCase("TestNode5300_No.json", InsightType.ClaimNotPayable, "Rotary Wing Air Transport Mileage for Rotary Wing Air Transport requires the billing for Rotary Wing Air Transport code A0431"),
    ClaimLineCase("TestNode5500_No.json", InsightType.ClaimNotPayable, "Non-Emergency transport code must be submitted with a corresponding mileage code with units greater than 0"),
    ClaimLineCase("TestNode5500_Yes.json", InsightType.ClaimLineValid, "Non-Emergency Rotary Wing Air Transport is payable"),
    ClaimLineCase("TestNode5600_No.json", InsightType.ClaimNotPayable, "Ground Transport Mileage for Ground Transport requires the billing for Ground Transport"),
    ClaimLineCase("TestNode5700_No.json", InsightType.ClaimNotPayable, "Non-Emergency transport code must be submitted with a corresponding mileage code with units greater than 0"),
    ClaimLineCase("TestNode5700_Yes.json", InsightType.ClaimLineValid, "Non-Emergency Ground Transport is payable"),
    ClaimLineCase("TestNode5800_No.json", InsightType.ClaimLineNotPayable, "Claim line Procedure may be inappropriate for this provider, manual review recommended"),
    ClaimLineCase("TestNode5900_No.json", InsightType.RecodeClaimLine, "Recode to Units = 2, Waiting time is reimbursed by payer up to 1 hour"),
    ClaimLineCase("TestNode6000_No.json", InsightType.ClaimLineNotPayable, "Waiting time can only be reimbursed by payer if the circumstances requiring waiting time and the exact time involved are documented in the information segment"),
    ClaimLineCase("TestNode6000_Yes.json", InsightType.ClaimLineValid, "Waiting time is payable (up to 1 hour)"),
    ClaimLineCase("TestNode6100_No.json", InsightType.ClaimLineNotPayable, "Claim line Procedure may be inappropriate for this provider, manual review recommended"),
    ClaimLineCase("TestNode6200_No.json", InsightType.RecodeClaimLine, "Recode to Units = 2, Waiting time is reimbursed by payer up to 1 hour"),
    ClaimLineCase("TestNode6300_No.json", InsightType.ClaimLineNotPayable, "Waiting time can only be reimbursed by payer if the circumstances requiring waiting time and the exact time involved are documented in the information segment"),
    ClaimLineCase("TestNode6300_Yes.json", InsightType.ClaimLineValid, "Waiting time is payable (up to 1 hour)"),
]

claim_line_tree = ambulance_decision_claim_line_tree()

@pytest.mark.parametrize("case", claim_line_cases, ids = [case.filename for case in claim_line_cases])
def test_claim_line_case(case: ClaimLineCase):
    case.testTree(claim_line_tree)
