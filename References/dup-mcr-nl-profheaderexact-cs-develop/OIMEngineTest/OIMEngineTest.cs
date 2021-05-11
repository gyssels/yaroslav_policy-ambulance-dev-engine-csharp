using System;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Newtonsoft.Json;
using OIMEngine;

namespace OIMEngineTest
{
    [TestClass]
    public class OIMEngineTest
    {
        [TestMethod]
        public void GetInsightTest()
        {
            string file = @"../../../test-claims/claim1.json";
            string Json = System.IO.File.ReadAllText(file);
            Schema.Common.Claim claim = JsonConvert.DeserializeObject<Schema.Common.Claim>(Json);
            Schema.InsightRequest.InsightEngineRequest req = new Schema.InsightRequest.InsightEngineRequest()
            {
                Claim = claim,
                TransactionId = Guid.NewGuid().ToString()
        };
            Schema.InsightResponse.InsightEngineResponse resp = new OIMEngine.OIMEngine().GetInsights(req);
            Assert.IsNotNull(resp);
            Assert.AreEqual(resp.Insights.Count, 1);
            Assert.AreEqual(resp.Insights[0].Id, claim.Id);
            Assert.AreEqual(resp.Insights[0].Type, Schema.Common.InsightType.ClaimLineValid);
            Assert.AreEqual(resp.Insights[0].Description, "Claim is valid according to this policy");
        }
    }
}
