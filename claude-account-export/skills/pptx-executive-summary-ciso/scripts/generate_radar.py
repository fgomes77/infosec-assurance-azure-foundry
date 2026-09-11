"""
Premium TPRM Spider Chart — clean version (no domain score pills below chart)
All scores shown as badges on the spider web spokes only.
Data-driven from JSON.
"""
import json, sys, argparse
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
import warnings; warnings.filterwarnings("ignore")

DOM_COL   = ["#1B3A6B","#1E5799","#2471A3","#2980B9","#3498DB"]
SCORE_COL = lambda s: "#B83228" if s>=5.5 else ("#C97A00" if s>=4.0 else "#1A6B3C")
TEAL,STROKE,GLOW = "#0E6B68","#12B5AF","#0FA39F"
BG,GRID_L,GRID_D,MUTED = "#FFFFFF","#CCE0DE","#96BCBA","#567370"
DOM_LABELS = ["Cybersecurity","Data\nManagement","IT","Business\nContinuity","Third-Parties"]
DOM_KEYS   = ["Cybersecurity","Data Management","IT","Business Continuity","Third-Parties"]

def generate(scores, out_path):
    N,MAX = 5,10
    angles = np.array([np.pi/2 - 2*np.pi*i/N for i in range(N)])
    ang_cl = np.append(angles, angles[0])
    def poly(r): return r*np.cos(ang_cl), r*np.sin(ang_cl)
    def pt(r,a): return r*np.cos(a), r*np.sin(a)

    fig = plt.figure(figsize=(4.8,4.4), facecolor=BG, dpi=320)
    ax  = fig.add_axes([0.05,0.04,0.90,0.92], facecolor=BG)
    ax.set_aspect("equal"); ax.axis("off")

    # Pentagon risk-zone fills
    for r,col,alpha in [(1.,"#FDECED",.52),(.70,"#FEF4E2",.58),(.40,"#E6F7EE",.64)]:
        px,py=poly(r); ax.fill(px,py,color=col,alpha=alpha,zorder=0)
    for r,col in [(1.,"#E8AAAA"),(.70,"#DEBA70"),(.40,"#7EC89A")]:
        px,py=poly(r); ax.plot(px,py,color=col,lw=.85,ls=(0,(4,3)),zorder=1,alpha=.75,solid_joinstyle="round")

    # Grid rings
    for g in [2,4,6,8,10]:
        f=g/MAX; px,py=poly(f)
        key=g in(4,6,8)
        ax.plot(px,py,color=GRID_D if key else GRID_L,
                lw=1.2 if key else .6,solid_capstyle="round",solid_joinstyle="round",zorder=2)

    # Spokes
    for a in angles: x,y=pt(1.,a); ax.plot([0,x],[0,y],color=GRID_D,lw=.85,zorder=2,alpha=.9)

    # Tick labels — upper-left spoke (Third-Parties, i=4)
    for g in [2,4,6,8,10]:
        tx,ty=pt(g/MAX,angles[4])
        ax.text(tx-.058,ty+.003,str(g),ha="right",va="center",fontsize=6.2,
                color=MUTED,fontweight="bold",fontfamily="DejaVu Sans",zorder=13,alpha=.9)

    # Data polygon — layered depth
    sc_cl=scores+[scores[0]]
    dpx=[s/MAX*np.cos(a) for s,a in zip(sc_cl,ang_cl)]
    dpy=[s/MAX*np.sin(a) for s,a in zip(sc_cl,ang_cl)]
    for exp,alp in [(.028,.07),(.016,.10),(.007,.13)]:
        gx=[v+exp*np.cos(ang_cl[i]) for i,v in enumerate(dpx)]
        gy=[v+exp*np.sin(ang_cl[i]) for i,v in enumerate(dpy)]
        ax.fill(gx,gy,color=GLOW,alpha=alp,zorder=3)
    ax.fill(dpx,dpy,color=TEAL,alpha=.13,zorder=4)
    ax.fill(dpx,dpy,color=TEAL,alpha=.20,zorder=4)
    ax.fill(dpx,dpy,color=TEAL,alpha=.17,zorder=4)
    line,=ax.plot(dpx,dpy,color=STROKE,lw=2.8,zorder=8,solid_capstyle="round",solid_joinstyle="round")
    line.set_path_effects([pe.SimpleLineShadow(shadow_color=GLOW,alpha=.38,offset=(.6,-.6),rho=.3),pe.Normal()])

    # Axis-end markers
    for i,a in enumerate(angles):
        x,y=pt(1.,a)
        ax.scatter(x,y,s=75,color=DOM_COL[i],alpha=.17,linewidths=0,zorder=6)
        ax.scatter(x,y,s=33,color=BG,linewidths=0,zorder=7)
        ax.scatter(x,y,s=19,color=DOM_COL[i],linewidths=0,zorder=8)

    # Data dots
    for i,(s,a) in enumerate(zip(scores,angles)):
        x,y=pt(s/MAX,a)
        ax.scatter(x,y,s=105,color=DOM_COL[i],alpha=.18,linewidths=0,zorder=7)
        ax.scatter(x,y,s=50,color=BG,linewidths=0,zorder=8)
        ax.scatter(x,y,s=29,color=DOM_COL[i],linewidths=0,zorder=9)

    # Score badges at r=0.80 per spoke
    NUDGE={0:.00,1:.10,2:.09,3:-.09,4:-.10}
    for i,(s,a) in enumerate(zip(scores,angles)):
        bx,by=pt(.80,a)
        perp=a+np.pi/2
        bx+=NUDGE[i]*np.cos(perp); by+=NUDGE[i]*np.sin(perp)
        bc=SCORE_COL(s)
        if s/MAX<.72:
            dx,dy=pt(s/MAX,a); ax.plot([dx,bx],[dy,by],color=bc,lw=.75,alpha=.35,ls=(0,(3,2)),zorder=11)
        ax.text(bx+.009,by-.011,f"{s}",ha="center",va="center",fontsize=10.5,
                fontweight="bold",color=bc,fontfamily="DejaVu Sans",alpha=.18,zorder=12,
                bbox=dict(boxstyle="round,pad=0.28",facecolor=bc,edgecolor="none",alpha=.12))
        ax.text(bx,by,f"{s}",ha="center",va="center",fontsize=10.5,
                fontweight="bold",color="white",fontfamily="DejaVu Sans",zorder=14,
                bbox=dict(boxstyle="round,pad=0.28",facecolor=bc,edgecolor="white",linewidth=.85,alpha=.97))

    # Domain labels
    LOFF={0:(0.,.24),1:(.29,.13),2:(.27,-.19),3:(-.27,-.19),4:(-.29,.13)}
    LHA={0:"center",1:"left",2:"left",3:"right",4:"right"}
    for i,(lab,a) in enumerate(zip(DOM_LABELS,angles)):
        x,y=pt(1.,a); ox,oy=LOFF[i]
        ax.text(x+ox,y+oy,lab,ha=LHA[i],va="center",fontsize=9.,fontweight="bold",
                color=DOM_COL[i],fontfamily="DejaVu Sans",linespacing=1.35,zorder=16,
                path_effects=[pe.withStroke(linewidth=4.5,foreground=BG)])

    ax.set_xlim(-1.60,1.60); ax.set_ylim(-1.55,1.56)
    plt.savefig(out_path,dpi=320,bbox_inches="tight",facecolor=BG,edgecolor="none")
    plt.close()
    print(f"✅  Radar saved → {out_path}")

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--data",  required=True)
    parser.add_argument("--output",required=True)
    args=parser.parse_args()
    with open(args.data) as f: d=json.load(f)
    scores=[d["domain_scores"].get(k,1.0) for k in DOM_KEYS]
    generate(scores,args.output)
