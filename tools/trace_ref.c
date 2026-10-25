/* Additive observer of the preserved strict C semantics, no state writeback.
 * The unchanged reference and original Olmstead execute separately as controls.
 * Each trace records ALL changed cells; final dump is all 59049 u16 LE cells.
 */
#define main preserved_reference_main
#include "../vendor/mb_ref.c"
#undef main

static unsigned short tape[59049], before[59049];

int main(int argc, char **argv) {
    if (argc != 5) return 1;
    unsigned long long budget = strtoull(argv[2], NULL, 10);
    FILE *source=fopen(argv[1], "rb"), *trace=fopen(argv[3], "wb"), *dump=fopen(argv[4], "wb");
    if (!source || !trace || !dump) return 1;
    unsigned n=0;
    int ch;
    while ((ch=fgetc(source)) != EOF) {
        if (isspace(ch)) continue;
        if (n>=59049 || ch<33 || ch>126 || !strchr("ji*p</vo",xlat1[(ch-33+n)%94])) return 1;
        tape[n++]=ch;
    }
    fclose(source);
    if (n<2) return 1;
    for (;n<59049;n++) tape[n]=op(tape[n-1],tape[n-2]);
    unsigned a=0,c=0,d=0,cursor=0;
    unsigned long long step=0;
    const char *terminal="BUDGET";
    int result=2;
    while (step<budget) {
        unsigned pa=a,pc=c,pd=d,pi=cursor;
        unsigned opcode=(tape[c]+c)%94;
        memcpy(before,tape,sizeof tape);
        const char *event_terminal="RUNNING";
        int emitted=-1;
        if (tape[c]<33 || tape[c]>126) {
            terminal=event_terminal="STALL"; result=3;
        } else {
            char instruction=xlat1[(tape[c]-33+c)%94];
            if (instruction=='j') d=tape[d];
            else if (instruction=='i') c=tape[d];
            else if (instruction=='*') a=tape[d]=tape[d]/3+(tape[d]%3)*19683;
            else if (instruction=='p') a=tape[d]=op(a,tape[d]);
            else if (instruction=='<') { emitted=a&255; putchar(emitted); }
            else if (instruction=='/') { int x=getchar(); a=x==EOF?59048:x; if(x!=EOF)cursor++; }
            else if (instruction=='v') { terminal=event_terminal="HALT"; result=0; }
            if (result==2) {
                if (tape[c]<33 || tape[c]>126) { terminal=event_terminal="STALL"; result=3; }
                else { tape[c]=(unsigned char)xlat2[tape[c]-33]; c=(c+1)%59049; d=(d+1)%59049; }
            }
        }
        fprintf(trace,"{\"step\":%llu,\"pre\":[%u,%u,%u,%u],\"opcode\":%u,\"post\":[%u,%u,%u,%u],\"changes\":[",step,pa,pc,pd,pi,opcode,a,c,d,cursor);
        int comma=0;
        for (unsigned k=0;k<59049;k++) if (before[k]!=tape[k]) {
            fprintf(trace,"%s[%u,%u,%u]",comma?",":"",k,before[k],tape[k]); comma=1;
        }
        fprintf(trace,"],\"output\":[");
        if(emitted>=0)fprintf(trace,"%d",emitted);
        fprintf(trace,"],\"terminal\":\"%s\"}\n",event_terminal);
        if (result!=2) break;
        step++;
    }
    for (unsigned k=0;k<59049;k++) { fputc(tape[k]&255,dump); fputc(tape[k]>>8,dump); }
    fclose(trace); fclose(dump);
    fprintf(stderr,"{\"terminal\":\"%s\",\"steps\":%llu,\"registers\":[%u,%u,%u,%u]}\n",terminal,step,a,c,d,cursor);
    return result;
}
