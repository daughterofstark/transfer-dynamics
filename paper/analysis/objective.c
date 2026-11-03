/* Matched separate-decay model, piecewise constant observed daily training.
 * Training state is divided by A so only two state derivatives propagate.
 * Output includes independently checkable per-visit predictions.
 */
#include <math.h>
#include <stdint.h>
typedef struct {double r,rg,rf,b,bg,bf;} Step;
static inline Step step(double p,double d,double kg,double kf){
  Step s;
  if(p==0){s.r=pow(1-kf,d);s.rg=0;s.rf=-d*s.r/(1-kf);s.b=s.bg=s.bf=0;return s;}
  double rate=p/d,z=exp(rate*log1p(-kg)),g=1-z,gg=rate*z/(1-kg);
  double r=1-g-kf,rg=-gg,rf=-1;
  if(r<1e-9){r=1e-9;rg=rf=0;}
  if(r>1-1e-12){r=1-1e-12;rg=rf=0;}
  double h=1-r,v=g/h,vg=gg/h+g*rg/(h*h),vf=g*rf/(h*h);
  s.r=pow(r,d);s.rg=d*s.r/r*rg;s.rf=d*s.r/r*rf;
  s.b=v*(1-s.r);s.bg=vg*(1-s.r)-v*s.rg;s.bf=vf*(1-s.r)-v*s.rf;
  return s;
}
double objective(int n,int m,const int64_t *ptr,const double *dt,const double *plays,
 const double *P,const double *D,const double *Y,const double *age,const double *W,
 const double *B,const double *x,int mode,double *grad,double *pred,double *eta){
  double kg=x[0],kf=x[1],A=x[2],q50=x[3],beta=x[4],kr=x[5],alpha=x[6],sw=0,total=0;
  double numerator=0,denominator=0,bgrad[7]={0};
  Step cached[4096];
  for(int k=0;k<4096;k++)cached[k]=step(k,1,kg,kf);
  for(int k=0;k<7;k++)grad[k]=0;
  for(int i=0;i<n;i++){
    if(W[i]==0)continue;
    double zz=0,zg=0,zf=0,H=0,Hf=0,Ha=0,egrad[7]={0},loss=0,bsum=0,bbgrad[7]={0};
    double aa=(age[i]-50)/20,factor=exp(beta*aa),q=q50*factor;int count=0;
    for(int j=0;j<m;j++){
      int ix=i*m+j;if(isnan(Y[ix]))continue;
      double d=D[ix],decay=pow(1-kr,d),previous=H;
      H=((1-alpha)*previous+1)*decay;
      Hf=(1-alpha)*Hf*decay-((1-alpha)*previous+1)*d*decay/(1-kr);
      Ha=((1-alpha)*Ha-previous)*decay;
      int64_t start=ptr[2*ix],end=ptr[2*ix+1];
      if(mode==0){start=0;end=1;}
      for(int64_t h=start;h<end;h++){
        double p=mode?plays[h]:P[ix],duration=mode?dt[h]:d;
        Step s;
        if(duration==1 && p>=0 && p<4096 && p==(int)p)s=cached[(int)p];
        else s=step(p,duration,kg,kf);
        double next=zz*s.r+s.b;
        zg=zg*s.r+zz*s.rg+s.bg;zf=zf*s.r+zz*s.rf+s.bf;zz=next;
        if(zz<0){zz=zg=zf=0;}else if(zz>1){zz=1;zg=zf=0;}
      }
      double value=A*zz+q*H,e=value-Y[ix];
      pred[ix]=value;loss+=e*e;count++;
      egrad[0]+=2*e*A*zg;egrad[1]+=2*e*A*zf;egrad[5]+=2*e*q*Hf;egrad[6]+=2*e*q*Ha;
      bsum+=B[i]*e;
      bbgrad[0]+=B[i]*A*zg;bbgrad[1]+=B[i]*A*zf;bbgrad[5]+=B[i]*q*Hf;bbgrad[6]+=B[i]*q*Ha;
      bbgrad[2]+=B[i]*zz;bbgrad[3]+=B[i]*factor*H;bbgrad[4]+=B[i]*q*aa*H;
      egrad[2]+=2*e*zz;egrad[3]+=2*e*factor*H;egrad[4]+=2*e*q*aa*H;
    }
    total+=W[i]*loss/count;sw+=W[i];
    numerator+=W[i]*bsum/count;denominator+=W[i]*B[i]*B[i];
    for(int k=0;k<7;k++){grad[k]+=W[i]*egrad[k]/count;bgrad[k]+=W[i]*bbgrad[k]/count;}
  }
  *eta=-numerator/denominator;
  for(int k=0;k<7;k++)grad[k]=(grad[k]+2*(*eta)*bgrad[k])/sw;
  return (total-numerator*numerator/denominator)/sw;
}
