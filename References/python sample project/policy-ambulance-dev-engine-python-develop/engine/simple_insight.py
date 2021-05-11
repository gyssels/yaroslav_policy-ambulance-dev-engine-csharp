from schema.insight_engine_response import InsightType

class SimpleInsight():
    """A class that represents a simple insight 
    that originates from the policy.
    """

    insight_type: InsightType = InsightType.Error
    text: str = ""

    def __init__(self, insight_type: InsightType, text: str):
        self.insight_type = insight_type
        self.text = text

    def __eq__(self, other):
        return self.insight_type == other.insight_type and self.text == other.text

    def __hash__(self):
        return hash((self.insight_type, self.text))

    def __repr__(self): 
            return str(self.insight_type) + ", " + self.text
    