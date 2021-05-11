from typing import cast, TypeVar
from typing import Callable, Set, List
from engine.tree_node import Predicate
from engine.code_set import CodeSet
from engine.code_sets import *
from engine.dsl import *
from engine.tree_node import TreeNode
from engine.tree_node import DecisionTreeNode
from engine.tree_node import ResultTreeNode
from fhir.resources.claim import Claim, ClaimItem, ClaimInsurance, ClaimSupportingInfo
from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.coding import Coding
from fhir.resources.period import Period
from fhir.resources.address import Address
from fhir.resources.organization import Organization


from schema.insight_engine_response import InsightEngineResponse, Insight, Defense, MessageBundle, TranslatedMessage
from schema.insight_engine_request import InsightEngineRequest
import json

alwaysTrue = Predicate("true", bool_always(True))

units_gt_1 = Predicate[ClaimLineFocus](
    "Does the claim line have units greater than 1?",
    lambda clf: units(clf) > 1)

exist_other_line_with_ET_and_same_trip_origin_destination = Predicate[ClaimLineFocus](
    "Does at least one claim line include modifier code = ET for the same date start and origin-destination modifier?",
    lambda clf:
        any(["ET" in modifiers(ocl.claim_line) and is_same_trip_based_on_origin_destination(clf, ocl)
            for ocl in other_lines(clf)])
)

is_there_pan = Predicate[ClaimLineFocus](
    "Is there a Prior Authorization Number (PAN) for the service?",
    lambda clf: any(
          par
            for i in claim(clf.request).insurance 
            if cast(ClaimInsurance, i).preAuthRef is not None
            for par in cast(ClaimInsurance, i).preAuthRef
        )
)

ocl_with_air_or_ground_transport_on_same_trip = Predicate[ClaimLineFocus](
    "Does the claim have a different claim line with a procedure code from the Air Transport code list or Ground Transport code list with a matching date of service from AND matching modifiers  (any combination, all for modifier fields)?",
    lambda clf: any([code(olf) in ground_and_air_transport_code_set.codes and is_same_trip(clf, olf) for olf in other_lines(clf)])
)

has_emergency_diagnosis = Predicate[ClaimLineFocus](
    "Does the Claim include a diagnosis code from the Emergency Medical Conditions Codes List?",
    lambda clf:
        not diagnosis_set(clf.request.claim).isdisjoint(emergency_medical_conditions_code_set.codes),
)

def is_clf_code_in_set(codeSet: CodeSet) -> Predicate[ClaimLineFocus]:
    return Predicate("Does the claim line have a procedure code listed in the " + codeSet.name + " Code List?",
        lambda clf: code(clf) in codeSet.codes
    )

def is_clf_code_equal_to(code1: str) -> Predicate[ClaimLineFocus]:
    return Predicate("Does the claim line have procedure code = " + code1 + "?",
        lambda clf: code(clf) == code1
    )

def is_there_ocl_code_on_same_trip(code1: str) -> Predicate[ClaimLineFocus]:
    return Predicate("Does the claim have a different claim line with a procedure code " + code1 + " with a matching date of service from AND matching modifiers (any combination, all for modifier fields)?",
            lambda clf: any(ocl for ocl in other_lines(clf) if 
                code(ocl) == code1 and 
                is_same_trip(clf, ocl)),
        )

def is_there_ocl_code_in_codeset_on_same_trip(code_set: CodeSet) -> Predicate[ClaimLineFocus]:
    if len(code_set.codes) == 1:
        return is_there_ocl_code_on_same_trip(list(code_set.codes)[0])
    else:
        return Predicate("Does the claim have a different claim line with a procedure code from " + code_set.name + " code list for the same trip?",
            lambda clf: any(ocl for ocl in other_lines(clf) if 
                code(ocl) in code_set.codes and 
                is_same_trip(clf, ocl)),
        )

def does_acl_code_have_units_greater(code1: str, amount: int) -> Predicate[ClaimLineFocus]:
    return Predicate(
        "Does the procedure code " + code1 + " have units greater than " + str(amount),
        lambda clf: units_of_code(clf.request, code1) > amount
    )

def does_cl_have_units_less_than(amount: int) -> Predicate[ClaimLineFocus]:
    return Predicate(
        "Does the claim line have units less than " + str(amount),
        lambda clf: units(clf) < amount
    )

def does_cl_contain_value_in_information_segment_for_same_trip() -> Predicate[ClaimLineFocus]:
    def f(clf: ClaimLineFocus) -> bool:
        supportingInfo = claim(clf.request).supportingInfo
        return supportingInfo is not None and any(
                (cast(Period, cast(ClaimSupportingInfo, si).timingPeriod).start == cast(Period, clf.claim_line.servicedPeriod).start)
                    and cast(ClaimSupportingInfo, si).valueString != ""
                for si in supportingInfo
            )
    return Predicate(
        "Does the claim line contain any value in the Information Segment for the Same Trip?",
        f,
    )
