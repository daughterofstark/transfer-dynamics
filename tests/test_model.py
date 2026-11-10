"""Independent recurrence, derivative, nesting, and held-out leakage checks."""
from pathlib import Path
import sys,unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'paper/analysis'))
import model as m
import fitting as f

def synthetic():
    rng=np.random.default_rng(230031);n=20;Y=np.full((n,4),np.nan);P=Y.copy();D=Y.copy();ptr=np.zeros((n,4,2),dtype=np.int64);dt=[];plays=[]
    for i in range(n):
        for j in range(1+i%4):
            ds=np.array([0.,1.,8.]);ps=np.array([i%3,4+j,0.])
            ptr[i,j]=[len(dt),len(dt)+3];dt.extend(ds);plays.extend(ps)
            P[i,j]=ps.sum();D[i,j]=ds.sum();Y[i,j]=rng.normal(3,4)
    age=np.linspace(20,85,n)
    return dict(Y=Y,P=P,D=D,ptr=ptr,dt=np.array(dt),plays=np.array(plays),age=age,GI0=100-.4*(age-50)+rng.normal(0,10,n),battery=np.full(n,17,dtype=np.int64))

class ModelTests(unittest.TestCase):
    def test_compiled_predictions_and_gradients(self):
        a=synthetic();w=np.linspace(.3,2,len(a['age']));b=f.center(a,f.reference(a,w))
        for alpha in [0.,.2]:
            x=np.array([.006,.005,4,1.6,-.5,.0006,alpha]);o=m.Objective(b,w);v,g=o(x)
            raw=m.reference_predict(b,x);z=(b['GI0']-100)/15
            eta=np.sum(w*z*np.nanmean(b['Y']-raw,axis=1))/np.sum(w*z*z)
            np.testing.assert_allclose(o.pred,raw+eta*z[:,None],atol=1e-10,rtol=0,equal_nan=True)
            for j in range(7):
                h=m.SCALE[j]*1e-5;dx=np.eye(7)[j]*h;fd=(o(x+dx)[0]-o(x-dx)[0])/(2*h)
                self.assertLess(abs((fd-g[j])*m.SCALE[j]),1e-6)
    def test_prediction_ignores_outcomes_and_uses_daily_timing(self):
        a=synthetic();x=np.array([.006,.005,4,1.6,-.5,.0006,0.]);coef=f.reference(a,np.ones(len(a['age'])))
        r=dict(parameters=dict(zip(m.NAMES,x)),reference_coefficients=coef,baseline_GI_coefficient_per15=-2.5)
        expected=m.reference_predict(a,x)-2.5*(f.center(a,coef)['GI0']-100)[:,None]/15
        p=f.predict(a,r);np.testing.assert_allclose(p,expected,atol=1e-11,rtol=0,equal_nan=True)
        other={**a,'Y':a['Y']+100};np.testing.assert_allclose(f.predict(other,r),p,atol=1e-11,rtol=0,equal_nan=True)
    def test_reference_excludes_heldout_baselines(self):
        a=synthetic();w=np.ones(len(a['age']));w[::4]=0
        other={**a,'GI0':a['GI0'].copy()};other['GI0'][::4]+=100
        np.testing.assert_allclose(f.reference(a,w),f.reference(other,w),atol=1e-11,rtol=0)
    def test_weighting_is_participant_mean_not_interval_mean(self):
        a=synthetic();w=np.linspace(.2,2,len(a['age']));o=m.Objective(a,w)
        loss,_=o(np.array([.006,.005,4,1.6,-.5,.0006,0.]))
        self.assertAlmostEqual(loss,np.average(np.nanmean((a['Y']-o.pred)**2,axis=1),weights=w),places=10)
    def test_zero_gameplay_keeps_retest_learning(self):
        a=synthetic();a['plays'][:]=0;a['P'][np.isfinite(a['P'])]=0
        x=np.array([.006,.005,4,1.6,-.5,.0006,0.]);p=m.reference_predict(a,x)
        np.testing.assert_allclose(p[:,0],1.6*np.exp(-.5*(a['age']-50)/20)*(1-.0006)**a['D'][:,0],atol=1e-12)
    def test_selected_comparisons_are_nested_and_no_outcome_leakage(self):
        import drift,slowing
        a=synthetic();w=np.linspace(.3,2,len(a['age']));x=np.array([.006,.005,4,1.6,-.5,.0006,0.])
        base=m.Objective(f.center(a,f.reference(a,w)),w);v,g=base(x)
        d=drift.Objective(a,w,drift=False);dv,dg=d(x)
        np.testing.assert_allclose(v,dv,atol=1e-9,rtol=0);np.testing.assert_allclose(g[:6],dg[:6],atol=1e-7,rtol=0)
        s=slowing.Objective(a,w,single=True);sv,sg=s(x[:6])
        np.testing.assert_allclose(v,sv,atol=1e-9,rtol=0);np.testing.assert_allclose(g[:6],sg,atol=1e-7,rtol=0)
        for alpha in [0.]:
            so=slowing.Objective(a,w);vv,gg=so(x[:6]);raw=slowing.python_raw(a,x[:6]);z=so.b
            eta=np.sum(w*z*np.nanmean(a['Y']-raw,axis=1))/np.sum(w*z*z)
            np.testing.assert_allclose(so.pred,raw+eta*z[:,None],atol=1e-9,rtol=0,equal_nan=True)
            for j in range(6):
                h=slowing.SCALE[j]*1e-5;dx=np.eye(6)[j]*h;fd=(so(x[:6]+dx)[0]-so(x[:6]-dx)[0])/(2*h)
                self.assertLess(abs((fd-gg[j])*slowing.SCALE[j]),1e-6)
    def test_same_date_tests_and_game_order(self):
        a=synthetic();a={k:(v[:1].copy() if k not in ['dt','plays'] else v) for k,v in a.items()}
        a.update(Y=np.array([[0.,0.,np.nan,np.nan]]),P=np.array([[3.,4.,np.nan,np.nan]]),D=np.array([[0.,0.,np.nan,np.nan]]),ptr=np.array([[[0,1],[1,2],[0,0],[0,0]]],dtype=np.int64),dt=np.array([0.,0.]),plays=np.array([3.,4.]),age=np.array([50.]),GI0=np.array([110.]))
        x=np.array([.006,.005,4,1.6,-.5,.0006,0.]);o=m.Objective(a,np.ones(1));o(x)
        raw=o.pred-o.eta[0]*(a['GI0'][:,None]-100)/15
        expected=np.array([4*(1-.994**3)+1.6,4*(1-.994**7)+3.2])
        np.testing.assert_allclose(raw[0,:2],expected,atol=1e-12)
    def test_maintenance_formula_matches_recurrence(self):
        x=np.array([.006,.005,4,1.6,-.5,.0006,0.]);d=m.derived(x)
        for fraction in [.7,.8,.9]:
            dose=d[f'dose_{int(fraction*100)}_games_day'];g=0.;ell=1-(1-x[0])**dose
            for day in range(10000):g=(g+ell*(x[2]-g))*(1-x[1])
            self.assertAlmostEqual(g,fraction*x[2],places=10)

if __name__=='__main__':unittest.main()
