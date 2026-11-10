#include <math.h>
#include <stdint.h>
#include <stdlib.h>
typedef struct {double r,rg,rf,b,bg,bf;} Step;
static inline Step step(double p,double d,double kg,double k,double u){
  Step s;double z=exp(p*log1p(-kg)),f=exp(d*u*log1p(-k));
  double zg=-p*z/(1-kg),ff=-d*u*f/(1-k);
  s.r=z*f;s.b=(1-z)*f;s.rg=zg*f;s.bg=-zg*f;
  s.rf=z*ff;s.bf=(1-z)*ff;return s;
}
double objective(int n,int m,int nq,const double *nodes,const double *weights,
 const int64_t *ptr,const double *dt,const double *plays,const double *D,
 const double *Y,const double *age,const double *W,const double *B,const double *x,
 int profile,double *grad,double *pred,double *eta){
  double kg=x[0],kf=x[1],A=x[2],q50=x[3],beta=x[4],kr=x[5],sw=0,total=0;
  double numerator=0,denominator=0,bgrad[6]={0};
  /* Calendar-day factors are reused across participants. */
  double *cache=malloc(sizeof(double)*4097*nq), zcache[4096];
  for(int p=0;p<4096;p++)zcache[p]=exp(p*log1p(-kg));
  for(int d=0;d<=4096;d++)for(int h=0;h<nq;h++)cache[d*nq+h]=exp(d*nodes[h]*log1p(-kf));
  for(int h=0;h<6;h++)grad[h]=0;
  for(int i=0;i<n;i++){
    if(W[i]==0)continue;
    double zz[128]={0},zg[128]={0},zf[128]={0},H=0,Hf=0,loss=0,egrad[6]={0},bsum=0,bbgrad[6]={0};
    double aa=(age[i]-50)/20,factor=exp(beta*aa),q=q50*factor;int count=0;
    for(int j=0;j<m;j++){
      int ix=i*m+j;if(isnan(Y[ix]))continue;
      double decay=pow(1-kr,D[ix]),previous=H;
      H=(H+1)*decay;Hf=Hf*decay-(previous+1)*D[ix]*decay/(1-kr);
      for(int64_t s=ptr[2*ix];s<ptr[2*ix+1];s++){
        double p=plays[s],d=dt[s],z=(p>=0 && p<4096 && p==(int)p)?zcache[(int)p]:exp(p*log1p(-kg));
        for(int h=0;h<nq;h++){
          double f=(d>=0 && d<=4096 && d==(int)d)?cache[(int)d*nq+h]:exp(d*nodes[h]*log1p(-kf));
          double dz=-p*z/(1-kg),ff=-d*nodes[h]*f/(1-kf);
          Step v={z*f,dz*f,z*ff,(1-z)*f,-dz*f,(1-z)*ff};
          double next=zz[h]*v.r+v.b;
          zg[h]=zg[h]*v.r+zz[h]*v.rg+v.bg;zf[h]=zf[h]*v.r+zz[h]*v.rf+v.bf;zz[h]=next;
        }
      }
      double z=0,zgg=0,zff=0;
      for(int h=0;h<nq;h++){z+=weights[h]*zz[h];zgg+=weights[h]*zg[h];zff+=weights[h]*zf[h];}
      double value=A*z+q*H,e=value-Y[ix],jac[6]={A*zgg,A*zff,z,factor*H,q*aa*H,q*Hf};
      pred[ix]=value;loss+=e*e;count++;bsum+=B[i]*e;
      for(int h=0;h<6;h++){egrad[h]+=2*e*jac[h];bbgrad[h]+=B[i]*jac[h];}
    }
    total+=W[i]*loss/count;sw+=W[i];numerator+=W[i]*bsum/count;denominator+=W[i]*B[i]*B[i];
    for(int h=0;h<6;h++){grad[h]+=W[i]*egrad[h]/count;bgrad[h]+=W[i]*bbgrad[h]/count;}
  }
  *eta=profile?-numerator/denominator:0;
  for(int h=0;h<6;h++)grad[h]=(grad[h]+2*(*eta)*bgrad[h])/sw;
  free(cache);return (total+(profile?-numerator*numerator/denominator:0))/sw;
}
