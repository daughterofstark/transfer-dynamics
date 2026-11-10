"""Scientific regression checks. All records are synthetic; no private inputs required."""
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
import pandas as pd
import composite_extract as ce
import data_build as db
import figures
import paper_pipeline as pp
import run_v17 as rv


class ReproductionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.quiet = redirect_stdout(io.StringIO())
        self.quiet.__enter__()
        self.addCleanup(self.quiet.__exit__, None, None, None)
        self.addCleanup(rv.ff.CONFIG.update, dict(rv.ff.CONFIG))
        self.source = self.root / "composite.csv"
        rows = []
        for run in (1, 2, 3):
            for sub, score in ((1,100), (2,110), (3,120)):
                rows.append(dict(USER_ID=1, TEST_RUN_ID=run, BRAINPOWER_TEST_ID=39,
                    NTH_RUN=run, INDEX_SCORE=score, TEST_SECTION_ID=sub,
                    DAYS_BETWEEN_TEST_RUNS=14, GAMEPLAYS_BETWEEN_TEST_RUNS=0,
                    TRESULT_CREATED_AT=f"2020-01-{run:02} 10:00:00"))
        rows.append(dict(rows[3], TEST_SECTION_ID=36, INDEX_SCORE=0,
                         GAMEPLAYS_BETWEEN_TEST_RUNS=161))
        rows.append(dict(rows[6], INDEX_SCORE=150, GAMEPLAYS_BETWEEN_TEST_RUNS=40,
                         TRESULT_CREATED_AT="2020-01-03 11:00:00"))
        pd.DataFrame(rows).to_csv(self.source,index=False)
        self.gi = self.root / "gi.csv"
        pd.DataFrame([dict(user_id=u,nth_test=i,battery_id=b,test_run_id=100*u+i,
                          normed_score=100+i,num_plays_before=10*(i-1),days_since_signup=70*(i-1))
                      for u,bs in ((10,[39,50]),(20,[39,39,50]),(30,[50,50]))
                      for i,b in enumerate(bs,1)]).to_csv(self.gi,index=False)

    def test_metadata_survives_zero_score_and_duplicate_removal(self):
        runs=ce.build_composite(self.source).set_index("test_run_id")
        self.assertEqual(runs.loc[2,"plays_btw"],161)
        self.assertEqual(runs.loc[3,"plays_btw"],40)
        self.assertEqual(runs.loc[3,"composite"],110)  # first attempt only
        self.assertTrue(runs.n_valid.eq(3).all())

    def test_battery_policy_is_explicit_and_same_battery_is_default(self):
        gi,_=pp.build_merged(self.gi,self.source,3,"NIC_",self.root/"merged.csv")
        self.assertEqual(gi.groupby("user_id").size().to_dict(),{10:1,20:2,30:2})
        retained,_=pp.build_merged(self.gi,self.source,3,"NIC_",self.root/"retain.csv",
                                   gi_battery_policy="retain")
        self.assertEqual(len(retained),7)
        frame=pd.read_csv(self.gi).drop(columns="battery_id")
        frame.to_csv(self.gi,index=False)
        with self.assertRaisesRegex(ValueError,"requires a nonmissing"):
            pp.build_merged(self.gi,self.source,3,"NIC_",self.root/"missing.csv")
        without,_=pp.build_merged(self.gi,self.source,3,"NIC_",self.root/"explicit.csv",
                                  gi_battery_policy="retain")
        self.assertEqual(len(without),7)

    def test_cache_rebuilds_after_input_policy_or_output_changes(self):
        args=SimpleNamespace(data=self.gi,composite=self.source,min_valid_subtests=3,
                             uid_prefix="NIC_",gi_battery_policy="retain",rebuild=False)
        with patch.object(db,"SCRATCH",str(self.root/"cache")):
            with patch.object(pp,"build_merged",wraps=pp.build_merged) as build:
                db.build_merged_once(args)
                db.build_merged_once(args)
                self.assertEqual(build.call_count,1)
                frame=pd.read_csv(self.gi); frame.loc[0,"normed_score"]+=1
                frame.to_csv(self.gi,index=False)
                db.build_merged_once(args)
                self.assertEqual(build.call_count,2)
                args.gi_battery_policy="same-battery"
                db.build_merged_once(args)
                self.assertEqual(build.call_count,3)
                (Path(db.SCRATCH)/"merged_cache.csv").write_text("corrupt cache")
                db.build_merged_once(args)
                self.assertEqual(build.call_count,4)

    def test_uncertainty_band_averages_individual_predictions(self):
        x=np.array([.0045704,.0021256,.3076,.0014601,3.0535,7.2487])
        params=dict(zip(rv.PO,x))
        P=np.array([[51.,60.],[400.,300.]])
        D=np.array([[70.,90.],[70.,150.]])
        center,band=figures.mean_model_trajectory(P,D,params,np.tile(x,(3,1)))
        expected=[]
        for p,d in zip(P,D):
            sd,st=figures._adv(params,0,0,d[0],p[0])
            sd2,st2=figures._adv(params,sd,st,d[1],p[1])
            expected.append([sd+st,sd2+st2])
        np.testing.assert_allclose(center,np.mean(expected,axis=0),rtol=0,atol=1e-12)
        np.testing.assert_allclose(band,np.tile(center,(2,1)),rtol=0,atol=1e-12)
        at_means=sum(figures._adv(params,0,0,D[:,0].mean(),P[:,0].mean()))
        self.assertGreater(abs(at_means-center[0]),.1)

    def test_failed_main_or_cv_fit_stops_before_results(self):
        bad=SimpleNamespace(success=False,fun=53.,x=np.array(rv.osman_start()),jac=np.zeros(6),
                            message="test failure",nit=1,nfev=7)
        arrays=[np.ones((10,2))]*3+[np.ones(10)]
        with patch.object(rv,"OUT",str(self.root)),patch.object(rv,"REPORT_PATH",str(self.root/"report.md")),patch.object(rv.ff,"_fit",return_value=bad):
            with self.assertRaisesRegex(RuntimeError,"did not converge"):
                rv.fit_and_check(*arrays,rv.osman_start(),"main")
            with self.assertRaisesRegex(RuntimeError,"fold 0"):
                rv.sec_cv(*arrays,rv.osman_start())
        self.assertFalse(json.loads((self.root/"cv_fit_diagnostics.json").read_text())[0]["success"])

    def test_parallel_bootstrap_preserves_serial_resampling(self):
        rng=np.random.default_rng(1)
        P=rng.uniform(0,500,(40,2)); D=rng.uniform(1,400,(40,2)); w=np.ones(40)
        x=np.array([.0045,.0021,.3,.0014,3.05,7.25])
        Y=rv.ff.simulate_matrix(P,D,x)+rng.normal(0,.03,P.shape)
        rv.ff.CONFIG["maxiter"]=10000
        outputs=[]
        for workers in (1,2):
            out=self.root/str(workers); out.mkdir()
            with patch.object(rv,"OUT",str(out)):
                outputs.append(rv.bootstrap(P,D,Y,w,x,3,7,workers=workers))
        np.testing.assert_allclose(outputs[0][0],outputs[1][0],rtol=0,atol=0,equal_nan=True)
        pd.testing.assert_frame_equal(outputs[0][1],outputs[1][1])
        self.assertTrue(outputs[0][1].success.any())


if __name__=="__main__":
    unittest.main()
