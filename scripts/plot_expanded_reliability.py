"""Standalone reliability figures from sanitized aggregate bins only."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]

def main():
    data=json.loads((ROOT/'research/data/expanded-20261005/experiment-v1/four-model-aggregate.json').read_text(encoding='utf-8'))
    fig,axes=plt.subplots(2,2,figsize=(10,8),constrained_layout=True)
    titles={'lr':'Logistic Regression','nb':'Multinomial Naive Bayes','svm':'Linear SVM','mbert':'Multilingual BERT'}
    colors=['#21618C','#117864','#884EA0','#B9770E']
    for ax,(name,color) in zip(axes.flat,zip(titles,colors)):
        r=data['results'][name];bins=[b for b in r['reliability_bins'] if b['count']]
        x=[b['mean_probability'] for b in bins];y=[b['observed_positive_rate'] for b in bins]
        ax.plot([0,1],[0,1],color='#9AA0A6',linestyle='--',linewidth=1,label='Perfect agreement')
        ax.plot(x,y,color=color,linewidth=1.5)
        ax.scatter(x,y,s=[20+b['count']*.6 for b in bins],color=color,edgecolor='white',linewidth=.6,zorder=3)
        ax.set(xlim=(-.03,1.03),ylim=(-.03,1.03),xlabel='Mean calibrated model score',ylabel='Observed source/rule positive rate',
            title=f'{titles[name]}\nBrier {r["brier"]:.4f} · log loss {r["log_loss"]:.4f}')
        ax.grid(alpha=.15);ax.spines[['top','right']].set_visible(False);ax.set_aspect('equal')
    fig.suptitle('SmishGuard · expanded retrospective test\n448 shared records; 10 equal-width bins; marker area reflects bin support',fontsize=13)
    fig.supxlabel('Source/rule labels are unconfirmed. Curves do not establish real-world probability calibration.',fontsize=9)
    fig.savefig(ROOT/'docs/expanded-reliability-20261005.png',dpi=180)
    fig.savefig(ROOT/'docs/expanded-reliability-20261005.svg')
    plt.close(fig)
    print('Reliability PNG and SVG saved from aggregate bins.')

if __name__=='__main__':main()
