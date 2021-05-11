from typing import cast, TypeVar
from typing import Callable, Set, List
from engine.tree_node import Predicate
from engine.code_set import CodeSet, TransportKind
from engine.code_sets import *
from engine.dsl import *
from engine.predicates import *
from engine.tree_node import TreeNode
from engine.tree_node import DecisionTreeNode
from engine.tree_node import ResultTreeNode

from fhir.resources.claim import Claim, ClaimItem, ClaimInsurance
from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.coding import Coding
from fhir.resources.period import Period
from fhir.resources.address import Address
from fhir.resources.organization import Organization

from schema.insight_engine_response import InsightEngineResponse, Insight, Defense, MessageBundle, TranslatedMessage
from schema.insight_engine_request import InsightEngineRequest
import json
import uuid

def ambulance_decision_claim_tree() -> TreeNode[InsightEngineRequest, SimpleInsight]:
    return node100()

def node100() -> TreeNode[InsightEngineRequest, SimpleInsight]:
    return DecisionTreeNode[InsightEngineRequest, SimpleInsight](
        "100",
        alwaysTrue,
        node200(),
        insight_deny_claim("Not Applicable, this policy is specific for TMHP Ambulance Claims submitted on the CMS-1500 paper claim form"),
    )

def node200() -> TreeNode[InsightEngineRequest, SimpleInsight]:
    return DecisionTreeNode[InsightEngineRequest, SimpleInsight](
        "200",
        Predicate("codes(request) have intersection with ground_and_air_transport_code_set", 
            lambda request: len(codes(request).intersection(ground_and_air_transport_code_set.codes)) > 0),
        node300(),
        insight_deny_claim("TMHP does not reimburse ambulance claims if a valid transport code is not present on the claim (if a client has not been transported)"),
    )

def node300() -> TreeNode[InsightEngineRequest, SimpleInsight]:
    return DecisionTreeNode[InsightEngineRequest, SimpleInsight](
        "300",
        Predicate("Does the claim have a valid Origin-Destination Modifier (in any modifier position) on every Claim Line?",
            lambda request:
                all([
                    len(
                        [m for m in modifiers(cl) if isOriginDestinationModifier(m)]
                    ) > 0
                    for cl in claimLines(request)
                ])
        ),
        stub("300:Yes"),
        insight_deny_claim("TMHP does not reimburse ambulance claims if a valid origin-destination modifier is not present on every claim line"),
    )

def ambulance_decision_claim_line_tree() -> TreeNode[ClaimLineFocus, SimpleInsight]:
    return node400()

def node400() -> TreeNode[ClaimLineFocus, SimpleInsight]:
    return DecisionTreeNode[ClaimLineFocus, SimpleInsight](
        "400",
        Predicate("Does the claim line have a valid CMS-1500 Place of Service Code?", has_valid_pos),
        node500(),
        insight_deny_claim("Invalid Place of Service for claim type CMS-1500 (paper claim)"),
    )

def node500() -> TreeNode[ClaimLineFocus, SimpleInsight]:
    return DecisionTreeNode[ClaimLineFocus, SimpleInsight](
        "500",
        Predicate("Does the claim line have the procedure code 92950?", lambda cl: code(cl) == "92950"),
        insight_deny_claim_line("Cardiopulmonary Resuscitation (CPR) is not separately payable and is included in ambulance transport fees"),
        node600(),
    )

def node600() -> TreeNode[ClaimLineFocus, SimpleInsight]:
    return DecisionTreeNode[ClaimLineFocus, SimpleInsight](
        "600",
        Predicate("Does the claim line have a procedure code in the Disposable Supplies Code List?",
            lambda cl: code(cl) in disposable_supplies_code_list),
        node700(),
        node800(),
    )

def node700() -> TreeNode[ClaimLineFocus, SimpleInsight]:
    return DecisionTreeNode[ClaimLineFocus, SimpleInsight](
        "700",
        Predicate("Does the claim have a different claim line with a procedure code A0434 with a matching date of service from AND matching modifiers (any combination, all for modifier fields)?",
            lambda clf: any([code(olf) == specialty_care_transport_code and is_same_trip(clf, olf) for olf in other_lines(clf)])),
        insight_deny_claim_line("Disposable Supplies are not Separately Payable when used during Specialty Care Transport"),
        node900(),
    )

def node800() -> TreeNode[ClaimLineFocus, SimpleInsight]:
    return DecisionTreeNode[ClaimLineFocus, SimpleInsight](
        "800",
        Predicate("Does the claim line have a procedure code in the Oxygen Supplies Code List?",
            lambda clf: code(clf) == oxygen_supplies_code),
        node1000(),
        node1100(),
    )

def node900() -> TreeNode[ClaimLineFocus, SimpleInsight]:
    return DecisionTreeNode[ClaimLineFocus, SimpleInsight](
        "900",
        ocl_with_air_or_ground_transport_on_same_trip,
        node1200(),
        insight_deny_claim_line("TMHP does not reimburse for disposable supplies when a transport did not occur for the same trip (matching dates and modifiers)"),
    )

def node1000() -> TreeNode[ClaimLineFocus, SimpleInsight]:
    return DecisionTreeNode[ClaimLineFocus, SimpleInsight](
        "1000",
        ocl_with_air_or_ground_transport_on_same_trip,
        node1300(),
        insight_deny_claim_line("TMHP does not reimburse for oxygen supplies when a transport did not occur for the same trip (matching dates and modifiers)"),
    )

def node1100() -> TreeNode[ClaimLineFocus, SimpleInsight]:
    return DecisionTreeNode[ClaimLineFocus, SimpleInsight](
        "1100",
        Predicate("Does the claim line have a procedure code in the Extra Attendant Code List?",
            lambda clf: code(clf) == extra_attendant_code),
        node1400(),
        node1500(),
    )

def node_max_units_1(node_id: str, supply: str, supplies: str) -> TreeNode[ClaimLineFocus, SimpleInsight]:
    return DecisionTreeNode[ClaimLineFocus, SimpleInsight](
        node_id,
        units_gt_1,
        insight_recode("Change Units to 1. " + supplies + " are only reimbursed once per trip for air or ground transport"),
        insight_payable(supply + " is payable."),
    )

def node1200() -> TreeNode[ClaimLineFocus, SimpleInsight]:
    return node_max_units_1("1200", "Disposable Supply", "Disposable Supplies")

def node1300() -> TreeNode[ClaimLineFocus, SimpleInsight]:
    return node_max_units_1("1300", "Oxygen Supply", "Oxygen Supplies")

def node1400() -> TreeNode[ClaimLineFocus, SimpleInsight]:
    return DecisionTreeNode[ClaimLineFocus, SimpleInsight](
        "1400",
        Predicate("Does the claim line have a Modifer (in any modifier position) equal to ET?",
            lambda clf: "ET" in modifiers(clf.claim_line)),
        node1600(),
        node1700(),
    )

def node1500() -> TreeNode[ClaimLineFocus, SimpleInsight]:
    return DecisionTreeNode[ClaimLineFocus, SimpleInsight](
        "1500",
        Predicate("Do all claim lines include modifier code = ET?",
            lambda clf:
                all(["ET" in modifiers(acl.claim_line)
                    for acl in all_lines(clf.request)])
        ),
        node1800(),
        node1900(),
    )

def node1600() -> TreeNode[ClaimLineFocus, SimpleInsight]:
    return DecisionTreeNode[ClaimLineFocus, SimpleInsight](
        "1600",
        ocl_with_air_or_ground_transport_on_same_trip,
        insight_payable("Extra Attendant is payable."),
        insight_deny_claim_line("TMHP does not reimburse for extra attendant when a transport did not occur for the same trip"),
    )

def node1700() -> TreeNode[ClaimLineFocus, SimpleInsight]:
    return DecisionTreeNode[ClaimLineFocus, SimpleInsight](
        "1700",
        exist_other_line_with_ET_and_same_trip_origin_destination,
        insight_deny_claim("If emergency transport is being claimed, then all claimed lines for the same trip must include the modifier ET."),
        node1725(),
    )

def node1725() -> TreeNode[ClaimLineFocus, SimpleInsight]:
    return DecisionTreeNode[ClaimLineFocus, SimpleInsight](
        "1725",
        ocl_with_air_or_ground_transport_on_same_trip,
        node2000(),
        insight_deny_claim_line("TMHP does not reimburse for an extra attendant without a corresponding Transport for the same trip"),
    )

def node1800() -> TreeNode[ClaimLineFocus, SimpleInsight]:
    return DecisionTreeNode[ClaimLineFocus, SimpleInsight](
        "1800",
        has_emergency_diagnosis,
        node2100(),
        insight_deny_claim("Emergency transport must include an approved ICD-10-CM code. Appeal required to prove emergency transport was provided."),
    )

def node1900() -> TreeNode[ClaimLineFocus, SimpleInsight]:
    return DecisionTreeNode[ClaimLineFocus, SimpleInsight](
        "1900",
        exist_other_line_with_ET_and_same_trip_origin_destination,
        insight_deny_claim("If emergency transport is being claimed, then all claimed lines for the same trip must include the modifier ET."),
        node2200(),
    )

def node2000() -> TreeNode[ClaimLineFocus, SimpleInsight]:
    return DecisionTreeNode[ClaimLineFocus, SimpleInsight](
        "2000",
        is_there_pan,
        insight_payable("Extra Attendant is payable."),
        insight_deny_claim("TMHP does not reimburse for a non-emergency extra attendant without a prior authorization on file"),
    )

def node2100() -> TreeNode[ClaimLineFocus, SimpleInsight]:
    return DecisionTreeNode[ClaimLineFocus, SimpleInsight](
        "2100",
        is_clf_code_in_set(ground_transport_code_set),
        node2300(),
        node2400(),
    )

def node2200() -> TreeNode[ClaimLineFocus, SimpleInsight]:
    return DecisionTreeNode[ClaimLineFocus, SimpleInsight](
        "2200",
        is_there_pan,
        node2500(),
        insight_deny_claim("If emergency transport is being claimed, then all claimed lines for the same trip must include the modifier ET."),
    )

def insight_no_corresponding_mileage(transport: str) -> ClaimLineInsight: 
    return insight_deny_claim(transport + " code must be submitted with a corresponding mileage code for same trip (matching dates and modifiers).")

def insight_zero_mileage(transport: str) -> ClaimLineInsight: 
    return insight_deny_claim(transport + " code must be submitted with a corresponding mileage code with units greater than 0")

def node2300() -> TreeNode[ClaimLineFocus, SimpleInsight]:
    return subtree_ground_mileage("Emergency")

def subtree_mileage(transport_kind: TransportKind, emergency: str) -> TreeNode[ClaimLineFocus, SimpleInsight]:
    return DecisionTreeNode[ClaimLineFocus, SimpleInsight](
        "2300(*)",
        is_there_ocl_code_on_same_trip(transport_kind.mileage_code),
        DecisionTreeNode[ClaimLineFocus, SimpleInsight](
            "2600(*)",
            does_acl_code_have_units_greater(transport_kind.mileage_code, 0),
            insight_payable(emergency + " " + transport_kind.transport_title + " is payable"),
            insight_zero_mileage(emergency + " transport"),
        ),
        insight_no_corresponding_mileage(emergency + " transport"),
    )

def subtree_ground_mileage(emergency: str) -> TreeNode[ClaimLineFocus, SimpleInsight]:
    return subtree_mileage(ground_transport, emergency) 

def subtree_fixed_wing_mileage(emergency: str) -> TreeNode[ClaimLineFocus, SimpleInsight]:
    return subtree_mileage(fixed_wing_transport, emergency) 

def subtree_rotary_wing_mileage(emergency: str) -> TreeNode[ClaimLineFocus, SimpleInsight]:
    return subtree_mileage(rotary_wing_transport, emergency) 

def node2400() -> TreeNode[ClaimLineFocus, SimpleInsight]:
    return DecisionTreeNode[ClaimLineFocus, SimpleInsight](
        "2400",
        is_clf_code_in_set(air_transport_code_set),
        node2700(),
        node4000(),
    )

def node2500() -> TreeNode[ClaimLineFocus, SimpleInsight]:
    return DecisionTreeNode[ClaimLineFocus, SimpleInsight](
        "2500",
        is_clf_code_in_set(ground_transport_code_set),
        node2800(),
        node2900(),
    )

def node2700():
    return DecisionTreeNode[ClaimLineFocus, SimpleInsight](
        "2700",
        is_clf_code_equal_to("A0431"),
        node3000(),
        node3100(),
    )

def node2800():
    return subtree_ground_mileage("Emergency")

def node2900():
    return DecisionTreeNode[ClaimLineFocus, SimpleInsight](
        "2900",
        is_clf_code_in_set(air_transport_code_set),
        node3300(),
        node4900(),
    )

def node3000():
    return subtree_rotary_wing_mileage("Emergency")

def node3100():
    return subtree_fixed_wing_mileage("Emergency")

def node3300():
    return DecisionTreeNode[ClaimLineFocus, SimpleInsight](
        "3300",
        is_clf_code_equal_to("A0431"),
        node3600(),
        node3700(),
    )

def node3600():
    return subtree_rotary_wing_mileage("Non-Emergency")

def node3700():
    return subtree_fixed_wing_mileage("Non-Emergency")

def node4000():
    return DecisionTreeNode[ClaimLineFocus, SimpleInsight](
        "4000",
        is_clf_code_equal_to("A0435"),
        node4100(),
        node4200(),
    )

def node4100():
    return DecisionTreeNode[ClaimLineFocus, SimpleInsight](
        "4100",
        is_there_ocl_code_on_same_trip("A0431"),
        node4300(),
        insight_deny_claim("Air Transport Mileage for Fixed Wing Air Transport requires the billing for Fixed Wing Air Transport A0431"),
    )

def node4200():
    return DecisionTreeNode[ClaimLineFocus, SimpleInsight](
        "4200",
        is_clf_code_equal_to("A0436"),
        node4400(),
        node4500(),
    )

def node4300():
    return DecisionTreeNode[ClaimLineFocus, SimpleInsight](
        "4300",
        does_acl_code_have_units_greater("A0435", 0),
        insight_payable("Mileage for Emergency Fixed Wing Air Transport is payable"),
        insight_deny_claim("Mileage code with units greater than 0 must be submitted with corresponding Emergency transport code."),
    )

def node4400():
    return DecisionTreeNode[ClaimLineFocus, SimpleInsight](
        "4400",
        is_there_ocl_code_on_same_trip("A0430"),
        node4600(),
        insight_deny_claim("Air Transport Mileage for Rotary Wing Air Transport requires the billing for Rotary Wing Air Transport A0430"),
    )


def node4500():
    return DecisionTreeNode[ClaimLineFocus, SimpleInsight](
        "4500",
        is_clf_code_equal_to("A0425"),
        node4700(),
        node5800(),
    )

def node4600():
    return DecisionTreeNode[ClaimLineFocus, SimpleInsight](
        "4600",
        does_acl_code_have_units_greater("A0436", 0),
        insight_payable("Emergency Rotary Wing Air Transport is payable"),
        insight_deny_claim("Emergency rotary wing air mileage code must be submitted  with units greater than 0"),
    )

def node4700():
    return DecisionTreeNode[ClaimLineFocus, SimpleInsight](
        "4700",
        is_there_ocl_code_in_codeset_on_same_trip(ground_transport_code_set),
        node4800(),
        insight_deny_claim("Ground Transport Mileage must be submitted with a corresponding Ground Transport code"),
    )

def node4800():
    return DecisionTreeNode[ClaimLineFocus, SimpleInsight](
        "4800",
        does_acl_code_have_units_greater("A0425", 0),
        insight_payable("Emergency Ground Transport is payable"),
        insight_deny_claim("Emergency ground mileage code must be submitted with units greater than 0"),
    )

def subtree_transport(transport_kind: TransportKind, emergency: str, continuation: TreeNode[ClaimLineFocus, SimpleInsight]) -> TreeNode[ClaimLineFocus, SimpleInsight]:
    return DecisionTreeNode[ClaimLineFocus, SimpleInsight](
        "4900(*)",
        is_clf_code_equal_to(transport_kind.mileage_code),
        DecisionTreeNode[ClaimLineFocus, SimpleInsight](
            "5000(*)",
            is_there_ocl_code_in_codeset_on_same_trip(transport_kind.transport_code_set),
            DecisionTreeNode[ClaimLineFocus, SimpleInsight](
                "5200(*)",
                does_acl_code_have_units_greater(transport_kind.mileage_code, 0),
                insight_payable(emergency + " " + transport_kind.transport_title + " is payable"),
                insight_deny_claim(emergency + " transport code must be submitted with a corresponding mileage code with units greater than 0")
            ),
            insight_deny_claim(transport_kind.transport_title + " Mileage for " + 
                transport_kind.transport_title + " requires the billing for " + transport_kind.transport_code_set.name)
        ),
        continuation,
    )

def node4900():
    return subtree_transport(fixed_wing_transport, "Non-Emergency", node5100())

def node5100():
    return subtree_transport(rotary_wing_transport, "Non-Emergency", node5400())

def node5400():
    return subtree_transport(ground_transport, "Non-Emergency", node6100())

def waiting_time_subtree() -> TreeNode[ClaimLineFocus, SimpleInsight]:
    return DecisionTreeNode[ClaimLineFocus, SimpleInsight](
        "5800, 6100",
        is_clf_code_equal_to(waiting_time_code),
        DecisionTreeNode[ClaimLineFocus, SimpleInsight](
            "5900, 6200",
            does_cl_have_units_less_than(3),
            DecisionTreeNode[ClaimLineFocus, SimpleInsight](
                "6000, 6300",
                does_cl_contain_value_in_information_segment_for_same_trip(),
                insight_payable("Waiting time is payable (up to 1 hour)"),
                insight_deny_claim_line("Waiting time can only be reimbursed by payer if the circumstances requiring waiting time and the exact time involved are documented in the information segment"),
            ),
            insight_recode("Recode to Units = 2, Waiting time is reimbursed by payer up to 1 hour"),
        ),
        insight_deny_claim_line("Claim line Procedure may be inappropriate for this provider, manual review recommended"),
    )

def node5800():
    return waiting_time_subtree() 

def node6100():
    return waiting_time_subtree() 

def ambulance_policy(request: InsightEngineRequest) -> InsightEngineResponse:
    claim_tree = ambulance_decision_claim_tree()
    claim_simple_insight = claim_tree(request)
    claim_line_tree = ambulance_decision_claim_line_tree()
    claim_line_insight_strs = [claim_line_tree(aclf) for aclf in all_lines(request)]

    res = InsightEngineResponse()
    res.insights = [create_insight(request, claim_simple_insight)] + list(map(lambda s: create_insight(request, s), claim_line_insight_strs))
    return res

def create_insight(request: InsightEngineRequest, claim_simple_insight: SimpleInsight) -> Insight:
    tmessage = TranslatedMessage()
    tmessage.lang = "en"
    tmessage.message = claim_simple_insight.text

    script = MessageBundle()
    script.uuid = str(uuid.uuid4())
    script.messages = [tmessage]

    defense = Defense()
    defense.script = script

    insight = Insight()
    insight.id = request.claim.id
    insight.description = claim_simple_insight.text
    insight.type = claim_simple_insight.insight_type
    insight.defense = defense

    return insight
