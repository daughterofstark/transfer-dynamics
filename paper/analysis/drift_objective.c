/* Matched separate-decay model, observed game counts and calendar-day forgetting.
 * Training state is divided by A so only two state derivatives propagate.
 * Output includes independently checkable per-visit predictions.
 */
#include <math.h>
#include <stdint.h>
typedef struct {double r,rg,rf,b,bg,bf;} Step;
static inline Step step(double p,double d,double kg,double kf){
  Step s;
  double z=exp(p*log1p(-kg)), f=exp(d*log1p(-kf));
  double zg=-p*z/(1-kg), ff=-d*f/(1-kf);
  s.r=z*f; s.b=(1-z)*f;
  s.rg=zg*f; s.bg=-zg*f;
  s.rf=z*ff; s.bf=(1-z)*ff;
  return s;
}
/* Profile baseline deviation and integrated age-dependent secular drift.
 * X has three columns per follow-up, M is inverse weighted X'X.
 * All state recurrences match the adopted observed-daily engine. */
double objective(int n,int m,const int64_t *ptr,const double *dt,const double *plays,
 const double *P,const double *D,const double *Y,const double *age,const double *W,
 const double *X,const double *M,const double *x,int mode,double *grad,double *pred,double *eta){
  double kg=x[0],kf=x[1],A=x[2],q50=x[3],beta=x[4],kr=x[5],sw=0,total=0;
  double numerator[3]={0},bgrad[3][6]={{0}};
  Step cached[4096];
  for(int k=0;k<4096;k++)cached[k]=step(k,1,kg,kf);
  for(int k=0;k<6;k++)grad[k]=0;
  for(int i=0;i<n;i++){
    if(W[i]==0)continue;
    double zz=0,zg=0,zf=0,H=0,Hf=0;
    double aa=(age[i]-50)/20,factor=exp(beta*aa),q=q50*factor;int count=0;
    for(int j=0;j<m;j++)if(!isnan(Y[i*m+j]))count++;
    double weight=W[i]/count;sw+=W[i];
    for(int j=0;j<m;j++){
      int ix=i*m+j;if(isnan(Y[ix]))continue;
      double d=D[ix],decay=pow(1-kr,d),previous=H;
      H=(H+1)*decay;Hf=Hf*decay-(previous+1)*d*decay/(1-kr);
      int64_t start=ptr[2*ix],end=ptr[2*ix+1];
      if(mode==0){start=0;end=1;}
      for(int64_t h=start;h<end;h++){
        double p=mode?plays[h]:P[ix],duration=mode?dt[h]:d;
        Step s;
        if(duration==1 && p>=0 && p<4096 && p==(int)p)s=cached[(int)p];
        else s=step(p,duration,kg,kf);
        double next=zz*s.r+s.b;
        zg=zg*s.r+zz*s.rg+s.bg;zf=zf*s.r+zz*s.rf+s.bf;zz=next;
      }
      double value=A*zz+q*H,e=value-Y[ix];
      double jac[6]={A*zg,A*zf,zz,factor*H,q*aa*H,q*Hf};
      pred[ix]=value;total+=weight*e*e;
      for(int k=0;k<6;k++)grad[k]+=2*weight*e*jac[k];
      for(int h=0;h<3;h++){
        double v=weight*X[ix*3+h];numerator[h]+=v*e;
        for(int k=0;k<6;k++)bgrad[h][k]+=v*jac[k];
      }
    }
  }
  for(int h=0;h<3;h++){
    eta[h]=0;
    for(int j=0;j<3;j++)eta[h]-=M[h*3+j]*numerator[j];
    total+=numerator[h]*eta[h];
  }
  for(int k=0;k<6;k++){
    for(int h=0;h<3;h++)grad[k]+=2*eta[h]*bgrad[h][k];
    grad[k]/=sw;
  }
  return total/sw;
}
