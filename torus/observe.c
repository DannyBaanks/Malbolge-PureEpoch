/* Independent, observational Classic VM. No state injection or restoration.
 * Build: gcc -O3 -std=c11 -Wall -Wextra observe.c -lcrypto -o observe
 * Usage: observe program max_steps output_prefix < input
 * SHA256 event stream is a canonical 32-byte little-endian record documented
 * in TORUS_RESULTS.md. Files export complete address sets, per-cell counts,
 * maximal delta-run histogram, first operand/write events, samples and edges.
 */
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <openssl/sha.h>
#define N 59049
#define NONE 65535
typedef unsigned long long U;
static uint16_t mem[N];
static const char enc[]="5z]&gqtyfr$(we4{WP)H-Zn,[%\\3dL+Q;>U!pJS72FhOA1CB6v^=I_0/8|jsb9m<.TVac`uY*MK'X~xDl}REokN:#?G\"i@";
static const unsigned char tab[3][3]={{1,0,0},{1,0,2},{2,2,1}};
static uint16_t crazy(uint16_t a,uint16_t b){unsigned v=0,p=1;for(int j=0;j<10;j++){v+=p*tab[b%3][a%3];a/=3;b/=3;p*=3;}return v;}
static int allowed(unsigned x){return x==4||x==5||x==23||x==39||x==40||x==62||x==68||x==81;}
static FILE *file(const char *base,const char *suffix){char p[4096];snprintf(p,sizeof p,"%s.%s",base,suffix);FILE*f=fopen(p,"wb");if(!f){perror(p);exit(9);}return f;}
typedef struct {U C,D,R,W,E,firstC,firstD,firstR,firstW,lastR,lastW;unsigned first_op_c,first_op,a,b;} Cell;
static Cell stat[N];
typedef struct {uint32_t key; U count,first,last;unsigned c_first;} Edge;
#define EH (1<<20)
static Edge edges[EH];
static void edge(unsigned from,unsigned to,unsigned c,U step){uint32_t k=(uint32_t)from*N+to+1;unsigned h=(k*2654435761u)&(EH-1);while(edges[h].key&&edges[h].key!=k)h=(h+1)&(EH-1);if(!edges[h].key){edges[h].key=k;edges[h].first=step;edges[h].c_first=c;}edges[h].count++;edges[h].last=step;}
static void u16(unsigned char*b,unsigned x){b[0]=x;b[1]=x>>8;}
static void u64(unsigned char*b,U x){for(int i=0;i<8;i++)b[i]=x>>(8*i);}
static void hashhex(unsigned char*d,char*s){for(int i=0;i<32;i++)sprintf(s+2*i,"%02x",d[i]);}
int main(int argc,char**argv){
 if(argc!=4)return 9;const char*base=argv[3];U max=strtoull(argv[2],0,10),step=0,opcount[94]={0};
 FILE *f=fopen(argv[1],"rb");if(!f){perror(argv[1]);return 9;}unsigned cells=0;int x;
 while((x=fgetc(f))!=EOF){if(isspace((unsigned char)x))continue;if(x<33||x>126||cells==N||!allowed((x+cells)%94)){fprintf(stderr,"INVALID_LOADER cell=%u byte=%d\n",cells,x);return 1;}mem[cells++]=x;}fclose(f);if(cells<2){fprintf(stderr,"TOO_SHORT\n");return 1;}
 for(unsigned i=cells;i<N;i++)mem[i]=crazy(mem[i-1],mem[i-2]);
 FILE*out=file(base,"stdout.bin"),*samples=file(base,"samples.csv"),*first=file(base,"first_events.csv");
 fprintf(samples,"step,a,c,d,cell,opcode,operand,direct_new,enc_addr,enc_old,enc_new,next_c,next_d,delta\n");
 fprintf(first,"kind,step,a,c,d,opcode,before,after,previous_c,previous_d,previous_opcode\n");
 uint16_t a=0,c=0,d=0;unsigned pc=NONE,pd=NONE,pop=NONE;const char*status="MAX_STEPS";
 U breaks4=0,breaks40=0,otherbreaks=0,diag=0,seglen=0,segments=1,cwrap=0,dwrap=0,collisions=0,uniquePairs=0,pairReturns=0,deltaReturns=0;
 U deltaFreq[N]={0},hist[100000]={0},maxseg=0,enc_total=0,write_total=0,read_total=0,inputs=0,outputs=0;
 unsigned char *pairs=calloc(((uint64_t)N*N+7)/8,1);if(!pairs)return 9;
 SHA256_CTX sha;SHA256_Init(&sha);unsigned char buffer[32768],digest[32];size_t bp=0;
 while(step<max){
  if(mem[c]<33||mem[c]>126){status="NONPRINTABLE_PC";break;}
  step++;unsigned cell=mem[c],op=(cell+c)%94,operand=mem[d],direct=NONE,ea=NONE,eb=NONE,en=NONE,oldc=c,oldd=d,olda=a;
  unsigned delta=(c+N-d)%N;deltaFreq[delta]++;opcount[op]++;
  if(stat[c].C++==0)stat[c].firstC=step;if(stat[d].D++==0)stat[d].firstD=step;
  if(c==d)collisions++;
  uint64_t pi=(uint64_t)c*N+d;unsigned char mask=1u<<(pi%8);if(pairs[pi/8]&mask)pairReturns++;else{pairs[pi/8]|=mask;uniquePairs++;}
  if(op==4||op==39||op==40||op==62){read_total++;Cell*s=&stat[d];if(s->R++==0)s->firstR=step;s->lastR=step;
   if(s->R<=2)fprintf(first,"read,%llu,%u,%u,%u,%u,%u,%u,%u,%u,%u\n",step,a,c,d,op,operand,operand,pc,pd,pop);
  }
  if(op==4)c=operand;
  else if(op==5){fputc(a&255,out);outputs++;}
  else if(op==23){int q=getchar();a=q==EOF?59048:q;inputs++;}
  else if(op==39){direct=operand/3+(operand%3)*19683;a=mem[d]=direct;}
  else if(op==40){d=operand;edge(oldd,(d+1)%N,oldc,step);}
  else if(op==62){direct=crazy(a,operand);a=mem[d]=direct;}
  if(direct!=NONE){write_total++;Cell*s=&stat[oldd];if(s->W++==0){s->firstW=step;s->first_op_c=oldc;s->first_op=op;s->a=operand;s->b=direct;}s->lastW=step;
   if(s->W<=2)fprintf(first,"write,%llu,%u,%u,%u,%u,%u,%u,%u,%u,%u\n",step,olda,oldc,oldd,op,operand,direct,pc,pd,pop);
  }
  if(op==81)status="HALTED";
  else{
   if(mem[c]<33||mem[c]>126){status="INVALID_ENCRYPTION";break;}
   ea=c;eb=mem[c];en=(unsigned char)enc[eb-33];mem[c]=en;stat[c].E++;enc_total++;
   if(c==N-1)cwrap++;if(d==N-1)dwrap++;c=(c+1)%N;d=(d+1)%N;
   unsigned nd=(c+N-d)%N;seglen++;
   if(nd!=delta){if(op==4)breaks4++;else if(op==40)breaks40++;else otherbreaks++;segments++;
    if(seglen>maxseg)maxseg=seglen;hist[seglen<100000?seglen:99999]++;seglen=0;
    if(deltaFreq[nd])deltaReturns++;
   }else diag++;
  }
  unsigned char rec[32];u64(rec,step);unsigned vals[12]={olda,oldc,oldd,cell,op,operand,direct,ea,eb,en,c,d};for(int j=0;j<12;j++)u16(rec+8+2*j,vals[j]);memcpy(buffer+bp,rec,32);bp+=32;if(bp==sizeof buffer){SHA256_Update(&sha,buffer,bp);bp=0;}
  if(step<=256||step%100000==0||op==81)fprintf(samples,"%llu,%u,%u,%u,%u,%u,%u,%u,%u,%u,%u,%u,%u,%u\n",step,olda,oldc,oldd,cell,op,operand,direct,ea,eb,en,c,d,delta);
  pc=oldc;pd=oldd;pop=op;if(op==81)break;
 }
 if(seglen>maxseg)maxseg=seglen;hist[seglen<100000?seglen:99999]++;SHA256_Update(&sha,buffer,bp);SHA256_Final(digest,&sha);char shahex[65];hashhex(digest,shahex);
 fclose(out);fclose(samples);fclose(first);free(pairs);
 FILE*sets=file(base,"sets.csv"),*counts=file(base,"counts.csv"),*eh=file(base,"d_edges.csv"),*dh=file(base,"delta.csv"),*sh=file(base,"segments.csv");
 fprintf(sets,"address,C,D,read,written,encrypted,intersection,union,complement,D_minus_C\n");
 fprintf(counts,"address,C_visits,D_visits,operand_reads,direct_writes,encryptions,firstC,firstD,firstR,firstW,lastR,lastW,first_write_c,first_write_opcode,first_write_before,first_write_after\n");
 U vc=0,vd=0,vr=0,vw=0,ve=0,inter=0,uni=0,dc=0,rw=0;unsigned char C[N];
 for(unsigned i=0;i<N;i++){Cell*s=&stat[i];unsigned cc=!!s->C,dd=!!s->D,rr=!!s->R,ww=!!s->W,ee=!!s->E;C[i]=cc;vc+=cc;vd+=dd;vr+=rr;vw+=ww;ve+=ee;inter+=cc&&dd;uni+=cc||dd;dc+=dd&&!cc;rw+=rr&&ww&&!cc;
 fprintf(sets,"%u,%u,%u,%u,%u,%u,%u,%u,%u,%u\n",i,cc,dd,rr,ww,ee,cc&&dd,cc||dd,!cc&&!dd,dd&&!cc);
 fprintf(counts,"%u,%llu,%llu,%llu,%llu,%llu,%llu,%llu,%llu,%llu,%llu,%llu,%u,%u,%u,%u\n",i,s->C,s->D,s->R,s->W,s->E,s->firstC,s->firstD,s->firstR,s->firstW,s->lastR,s->lastW,s->first_op_c,s->first_op,s->a,s->b);
 }
 fprintf(eh,"from_d,to_d_after_increment,count,first_step,last_step,first_c\n");for(unsigned i=0;i<EH;i++)if(edges[i].key){unsigned k=edges[i].key-1;fprintf(eh,"%u,%u,%llu,%llu,%llu,%u\n",k/N,k%N,edges[i].count,edges[i].first,edges[i].last,edges[i].c_first);}
 fprintf(dh,"delta_c_minus_d,count\n");unsigned deltas=0;for(unsigned i=0;i<N;i++)if(deltaFreq[i]){fprintf(dh,"%u,%llu\n",i,deltaFreq[i]);deltas++;}
 fprintf(sh,"transition_length,count\n");for(unsigned i=0;i<100000;i++)if(hist[i])fprintf(sh,"%u,%llu\n",i,hist[i]);
 unsigned period=N;for(unsigned p=1;p<=N;p*=3){int yes=1;for(unsigned j=p;j<N;j++)if(C[j]!=C[j%p]){yes=0;break;}if(yes){period=p;break;}}
 FILE*json=file(base,"json");fprintf(json,"{\n\"status\":\"%s\",\"steps\":%llu,\"cells_source\":%u,\"event_sha256\":\"%s\",\n",status,step,cells,shahex);
 fprintf(json,"\"visited_c\":%llu,\"visited_d\":%llu,\"intersection\":%llu,\"union\":%llu,\"complement\":%llu,\"D_minus_C\":%llu,\"read_unique\":%llu,\"written_unique\":%llu,\"encrypted_unique\":%llu,\"read_written_not_C\":%llu,\n",vc,vd,inter,uni,(U)N-uni,dc,vr,vw,ve,rw);
 fprintf(json,"\"read_events\":%llu,\"direct_write_events\":%llu,\"encryption_hits\":%llu,\"inputs\":%llu,\"output_len\":%llu,\n",read_total,write_total,enc_total,inputs,outputs);
 fprintf(json,"\"delta_segments\":%llu,\"break4\":%llu,\"break40\":%llu,\"break_other\":%llu,\"diagonal_steps\":%llu,\"diagonal_fraction\":%.12f,\"max_segment_transitions\":%llu,\"distinct_deltas\":%u,\"delta_reentries\":%llu,\n",segments,breaks4,breaks40,otherbreaks,diag,step?(double)diag/step:0,maxseg,deltas,deltaReturns);
 fprintf(json,"\"increment_wrap_c\":%llu,\"increment_wrap_d\":%llu,\"simultaneous_c_eq_d\":%llu,\"unique_projected_pairs\":%llu,\"projected_pair_revisits\":%llu,\"C_min_cyclic_period\":%u,\"C_shift_symmetry_count_correct\":%u,\n\"opcodes\":{",cwrap,dwrap,collisions,uniquePairs,pairReturns,period,N/period-1);
 int comma=0;for(int i=0;i<94;i++)if(opcount[i]){fprintf(json,"%s\"%d\":%llu",comma?",":"",i,opcount[i]);comma=1;}fprintf(json,"}}\n");
 fclose(json);fclose(sets);fclose(counts);fclose(eh);fclose(dh);fclose(sh);fprintf(stderr,"%s steps=%llu union=%llu intersection=%llu\n",status,step,uni,inter);return strcmp(status,"HALTED")?2:0;
}
