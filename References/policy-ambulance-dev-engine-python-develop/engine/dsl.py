from typing import cast, TypeVar
from typing import Callable, Set, List
from engine.tree_node import Predicate
from engine.code_set import CodeSet
from engine.code_sets import *
from engine.tree_node import TreeNode
from engine.tree_node import DecisionTreeNode
from engine.tree_node import ResultTreeNode
from fhir.resources.claim import Claim, ClaimItem, ClaimInsurance, ClaimDiagnosis
from fhir.resources.fhirtypes import DateTime, CodingType, QuantityType, ClaimDiagnosisType
from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.coding import Coding
from fhir.resources.period import Period
from fhir.resources.quantity import Quantity
from fhir.resources.address import Address
from fhir.resources.organization import Organization

from schema.insight_engine_response import InsightEngineResponse, Insight, Defense, MessageBundle, TranslatedMessage
from schema.insight_engine_request import InsightEngineRequest
import json

from engine.simple_insight import SimpleInsight
from schema.insight_engine_response import InsightType

A = TypeVar('A')

ClaimLine = ClaimItem

class ClaimLineFocus():
    def __init__(self, claim_line: ClaimItem, request: InsightEngineRequest):
        self.claim_line = claim_line
        self.request = request

ClaimLineInsight = ResultTreeNode[ClaimLineFocus, SimpleInsight]

def stub(id: str) -> ResultTreeNode[A, SimpleInsight]:
    return ResultTreeNode[A, SimpleInsight](lambda request: SimpleInsight(InsightType.Error, "TODO: "+id))

# def insight(s: str) -> TreeNode[A, str]:
#     return insight_deny(s)

def insight_payable(s: str) -> ResultTreeNode[A, SimpleInsight]:
    return ResultTreeNode[A, SimpleInsight](lambda request: SimpleInsight(InsightType.ClaimLineValid, s))

def insight_deny_claim(s: str) -> ResultTreeNode[A, SimpleInsight]:
    return ResultTreeNode[A, SimpleInsight](lambda request: SimpleInsight(InsightType.ClaimNotPayable, s))

def insight_deny_claim_line(s: str) -> ResultTreeNode[A, SimpleInsight]:
    return ResultTreeNode[A, SimpleInsight](lambda request: SimpleInsight(InsightType.ClaimLineNotPayable, s))

def insight_recode(s: str) -> ResultTreeNode[A, SimpleInsight]:
    return ResultTreeNode[A, SimpleInsight](lambda request: SimpleInsight(InsightType.RecodeClaimLine, s))

def bool_always(res: bool) -> Callable[[InsightEngineRequest], bool]:
    return lambda request: res

def claim(request: InsightEngineRequest) -> Claim:
    return request.claim

def claimLines(request: InsightEngineRequest) -> List[ClaimItem]:
    return cast(List[ClaimItem], cast(Claim, request.claim).item)

def codes(request: InsightEngineRequest) -> set:
    return set([cast(Coding, c).code
        for acl in claimLines(request)
        for c in cast(CodeableConcept, acl.productOrService).coding])

def isOriginDestinationModifier(s: str) -> bool:
    return  (len(s) == 2) and (s[0] in origin_letters) and (s[1] in destination_letters)

def modifiers(cl: ClaimItem) -> List[str]:
    return [
        coding.code
            for codings in [cast(List[Coding], c.coding) for c in cast(List[CodeableConcept], cl.modifier)]
                for coding in codings
    ]

def pos(cl: ClaimItem) -> List[str]:
    if cl.locationCodeableConcept is None:
        return []
    else:
        return [cast(Coding, c).code for c in cast(CodeableConcept, cl.locationCodeableConcept).coding]

def has_valid_pos(clf: ClaimLineFocus) -> bool:
    return not cms1500_places_of_service_code_set.codes.isdisjoint(set(pos(clf.claim_line)))

def code(clf: ClaimLineFocus) -> str:
    codes = cast(List[Coding], cast(CodeableConcept, clf.claim_line.productOrService).coding)
    assert len(codes) == 1
    code = codes[0].code
    #print("Code = " + str(code))
    return code

def origin_destination_modifiers(self: ClaimItem) -> List[str]:
    return [m for m in modifiers(self) if isOriginDestinationModifier(m)]

def is_same_start_date(self: ClaimLineFocus, other: ClaimLineFocus) -> bool:
    period_start_same = (cast(Period, self.claim_line.servicedPeriod).start == cast(Period, other.claim_line.servicedPeriod).start)
    # print("self .claim_line.servicedPeriod.start.isostring = " + str(self .claim_line.servicedPeriod.start.isostring))
    # print("other.claim_line.servicedPeriod.start.isostring = " + str(other.claim_line.servicedPeriod.start.isostring))
    # print("is_same_start_date = " + str(period_start_same))
    return period_start_same

def is_matching_modifiers(self: ClaimLineFocus, other: ClaimLineFocus) -> bool:
    self_modifiers = modifiers(self.claim_line)
    other_modifiers = modifiers(other.claim_line)
    modifiers_same = set(self_modifiers) == set(other_modifiers)
    # print("is_matching_modifiers = " + str(modifiers_same))
    return modifiers_same

def is_matching_origin_destination_modifiers(self: ClaimLineFocus, other: ClaimLineFocus) -> bool:
    self_modifiers = origin_destination_modifiers(self.claim_line)
    other_modifiers = origin_destination_modifiers(other.claim_line)
    modifiers_same = set(self_modifiers) == set(other_modifiers)
    return modifiers_same

def is_same_trip(self: ClaimLineFocus, other: ClaimLineFocus) -> bool:
    return is_same_start_date(self, other) and is_matching_modifiers(self, other)

def is_same_trip_based_on_origin_destination(self: ClaimLineFocus, other: ClaimLineFocus) -> bool:
    return is_same_start_date(self, other) and is_matching_origin_destination_modifiers(self, other)

def all_lines(request: InsightEngineRequest) -> List[ClaimLineFocus]:
    return [ClaimLineFocus(i, request) for i in request.claim.item]

def other_lines(clf: ClaimLineFocus) -> List[ClaimLineFocus]:
    return [ocl for ocl in all_lines(clf.request) if ocl.claim_line != clf.claim_line]

def units(clf: ClaimLineFocus) -> int:
    return int(cast(Quantity, clf.claim_line.quantity).value)

def diagnoses(c: Claim) -> List[str]:
    return [cast(Coding, c).code
        for d in c.diagnosis
        for c in cast(CodeableConcept, cast(ClaimDiagnosis, d).diagnosisCodeableConcept).coding]

def diagnosis_set(c: Claim) -> Set[str]:
    return set(diagnoses(c))

def units_of_code(self: InsightEngineRequest, code1: str) -> int:
    return sum(units(alf) for alf in all_lines(self) if code(alf) == code1)
