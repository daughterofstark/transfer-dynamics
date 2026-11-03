#include <math.h>
#include <stdint.h>
#include <stdlib.h>
typedef struct {double r,rg,rf,b,bg,bf;} Step;
static inline Step step(double p,double d,double kg,double k,double u){
  Step s;double lam=-log1p(-k)*u,dk=u*exp(-lam)/(1-k);
  if(p==0){s.r=exp(-lam*d);s.rg=0;s.rf=-d*u*s.r/(1-k);s.b=s.bg=s.bf=0;return s;}
  double rate=p/d,z=exp(rate*log1p(-kg)),g=1-z,gg=rate*z/(1-kg);
  double r=exp(-lam)-g,rg=-gg,rf=-dk;
  if(r<1e-9){r=1e-9;rg=rf=0;}
  if(r>1-1e-12){r=1-1e-12;rg=rf=0;}
  double h=1-r,v=g/h,vg=gg/h+g*rg/(h*h),vf=g*rf/(h*h);
  s.r=pow(r,d);s.rg=d*s.r/r*rg;s.rf=d*s.r/r*rf;
  s.b=v*(1-s.r);s.bg=vg*(1-s.r)-v*s.rg;s.bf=vf*(1-s.r)-v*s.rf;
  return s;
}
double objective(int n,int m,int nq,const double *nodes,const double *weights,
 const int64_t *ptr,const double *dt,const double *plays,const double *D,
 const double *Y,const double *age,const double *W,const double *B,const double *x,
 int profile,double *grad,double *pred,double *eta){
  double kg=x[0],kf=x[1],A=x[2],q50=x[3],beta=x[4],kr=x[5],sw=0,total=0;
  double numerator=0,denominator=0,bgrad[6]={0};
  Step *cache=malloc(sizeof(Step)*129*nq);
  for(int p=0;p<129;p++)for(int h=0;h<nq;h++)cache[p*nq+h]=step(p,1,kg,kf,nodes[h]);
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
        double p=plays[s],d=dt[s];int cached=d==1 && p>=0 && p<129 && p==(int)p;
        for(int h=0;h<nq;h++){
          Step v=cached?cache[(int)p*nq+h]:step(p,d,kg,kf,nodes[h]);
          double next=zz[h]*v.r+v.b;
          zg[h]=zg[h]*v.r+zz[h]*v.rg+v.bg;zf[h]=zf[h]*v.r+zz[h]*v.rf+v.bf;zz[h]=next;
          if(zz[h]<0){zz[h]=zg[h]=zf[h]=0;}else if(zz[h]>1){zz[h]=1;zg[h]=zf[h]=0;}
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
