import tempfile,unittest
from pathlib import Path
from haunted_blender import motion_organ,motion_executor
from haunted_blender.motion_atlas_bridge import import_route_proposals

class MotionExecutor007Tests(unittest.TestCase):
    def setup_route(self,root):
        req=motion_organ.freeze_request(root,scene_id="s7",scene_sha256="a"*64,window_id="w7",start_seconds=1,duration_seconds=2,prompt="wake",source_address="sha256:"+"b"*64,remote_disclosure_approved=True)
        offers=motion_organ.freeze_offers(root,{"schema":motion_organ.OFFERS_SCHEMA,"observedAt":"2026-10-06T00:00:00Z","offers":[
            {"offerId":"free-a","providerId":"a","model":"a1","available":True,"spendClass":"free","creditCost":1,"creditBalance":10,"inputModes":["image-to-video"],"aspectRatios":["16:9"],"minSeconds":1,"maxSeconds":8},
            {"offerId":"paid-b","providerId":"b","model":"b1","available":True,"spendClass":"paid","estimatedUsdMicros":50000,"inputModes":["image-to-video"],"aspectRatios":["16:9"],"minSeconds":1,"maxSeconds":8}]})
        route=motion_organ.route_request(root,req["request"],offers["offers"])
        return motion_executor.build_plan(root,route["route"],occurrence_budget_usd_micros=100000,per_job_budget_usd_micros=75000)
    def caps(self,offer,provider,model):
        return {"schema":motion_executor.CAP_SCHEMA,"offerId":offer,"providerId":provider,"model":model,"available":True,"inputModes":["image-to-video"],"aspectRatios":["16:9"],"minSeconds":1,"maxSeconds":8}
    def quote(self,offer,usd=None,generated=4,denom="provider-credits"):
        return {"schema":motion_executor.QUOTE_SCHEMA,"offerId":offer,"exactConfiguration":True,"generatedDurationSeconds":generated,"denomination":denom,"amount":1,"wholeJobUsdMicros":usd}
    def test_ambiguous_timeout_blocks_fallthrough(self):
        with tempfile.TemporaryDirectory() as td:
            r=Path(td);p=self.setup_route(r)
            s=motion_executor.record_capabilities(r,p["plan"],p["state"],self.caps("free-a","a","a1"))
            s=motion_executor.record_quote(r,p["plan"],s["state"],self.quote("free-a",0))
            s=motion_executor.record_submit(r,p["plan"],s["state"],{"schema":motion_executor.SUBMIT_SCHEMA,"offerId":"free-a","vendorRequestId":"job-1","submittedParameterSha256":"c"*64})
            s=motion_executor.record_status(r,p["plan"],s["state"],{"schema":motion_executor.STATUS_SCHEMA,"offerId":"free-a","vendorRequestId":"job-1","status":"timeout"})
            self.assertEqual(motion_executor.next_action(r,p["plan"],s["state"])["status"],"reconcile_required")
            with self.assertRaises(ValueError): motion_executor.advance(r,p["plan"],s["state"])
    def test_definitive_failure_allows_next_provider(self):
        with tempfile.TemporaryDirectory() as td:
            r=Path(td);p=self.setup_route(r)
            s=motion_executor.record_capabilities(r,p["plan"],p["state"],self.caps("free-a","a","a1"))
            s=motion_executor.record_quote(r,p["plan"],s["state"],self.quote("free-a",0))
            s=motion_executor.record_submit(r,p["plan"],s["state"],{"schema":motion_executor.SUBMIT_SCHEMA,"offerId":"free-a","vendorRequestId":"job-1","submittedParameterSha256":"c"*64})
            s=motion_executor.record_status(r,p["plan"],s["state"],{"schema":motion_executor.STATUS_SCHEMA,"offerId":"free-a","vendorRequestId":"job-1","status":"definitively_failed"})
            s=motion_executor.advance(r,p["plan"],s["state"])
            self.assertEqual(s["stateBody"]["currentAttempt"],2)
    def test_generated_job_length_is_preserved(self):
        with tempfile.TemporaryDirectory() as td:
            r=Path(td);p=self.setup_route(r)
            s=motion_executor.record_capabilities(r,p["plan"],p["state"],self.caps("free-a","a","a1"))
            s=motion_executor.record_quote(r,p["plan"],s["state"],self.quote("free-a",0,6))
            self.assertEqual(s["stateBody"]["attempts"][0]["generatedDurationSeconds"],6)
    def test_paid_quote_budget_blocks_before_submit(self):
        with tempfile.TemporaryDirectory() as td:
            r=Path(td);p=self.setup_route(r)
            bad=self.caps("free-a","a","a1");bad["available"]=False
            s=motion_executor.record_capabilities(r,p["plan"],p["state"],bad)
            s=motion_executor.advance(r,p["plan"],s["state"])
            s=motion_executor.record_capabilities(r,p["plan"],s["state"],self.caps("paid-b","b","b1"))
            s=motion_executor.record_quote(r,p["plan"],s["state"],self.quote("paid-b",80000,4,"USD"))
            self.assertEqual(s["stateBody"]["status"],"budget_blocked")
    def test_atlas_import_never_authorizes_execution(self):
        sample={"schema":"haunted-blender/motion-route-proposals/v0","request":{"window_id":"w"},"proposals":[{"endpoint_id":"x","state":"proposal-only","indicative_usd":.01,"quote_unit":"seconds","proposed_generate_seconds":2,"window_seconds":2,"exact_configuration_quote":"unresolved","account_access":"unresolved","spend_authorized":False,"candidate_accepted":False,"requires":[]}],"fallback_on_ambiguous_submission":"STOP_AND_RECONCILE_EXISTING_JOB","generation_submitted":False,"editorial_authority":"human + existing Blender accepted-video-resolver/v0"}
        imp=import_route_proposals(sample,atlas_package_sha256="d"*64,observed_at="2026-10-06T00:00:00Z")
        self.assertFalse(imp["targets"][0]["executionEligible"])
        self.assertTrue(imp["targets"][0]["refreshRequired"])
if __name__=="__main__": unittest.main()
