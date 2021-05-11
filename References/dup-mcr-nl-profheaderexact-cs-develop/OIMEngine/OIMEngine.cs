using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using System.Linq;

namespace OIMEngine {
    public class OIMEngine
    {
        
        public Schema.InsightResponse.InsightEngineResponse GetInsights(Schema.InsightRequest.InsightEngineRequest req)
        {
            var retval = new Schema.InsightResponse.InsightEngineResponse();

            retval.Insights = new List<Schema.Common.Insight>();
            if (req.Claim.Id.StartsWith("for") && req.Claim.Id != "forDotNet") {
                return retval;
            }

            var message = new Schema.Common.TranslatedMessage() {
                Lang = "en",
                Message = "This policy does not perform any actual checks."
            };

            var script = new Schema.Common.MessageBundle();
            script.Uuid = Guid.NewGuid().ToString();
            script.Messages = new List<Schema.Common.TranslatedMessage>() { message };

            retval.Insights.Add(new Schema.Common.Insight()
            {
                Id = req.Claim.Id,
                Type = Schema.Common.InsightType.ClaimLineValid,
                Description = "Claim is valid according to this policy",
                Defense = new Schema.Common.Defense() { Script = script }
            }) ;

            return retval;
        }
    }
}
