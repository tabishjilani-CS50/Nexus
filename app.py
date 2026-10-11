from flask import Flask, render_template, request, redirect, url_for, send_file
import csv, os
from datetime import datetime
from io import BytesIO

app = Flask(__name__)
TRANSACTION_FILE = 'nexus_transactions.csv'
BUDGET_FILE = 'nexus_budgets.csv'

def setup():
    if not os.path.exists(TRANSACTION_FILE):
        with open(TRANSACTION_FILE,'w',newline='',encoding='utf-8') as f: csv.writer(f).writerow(['id','date','type','category','amount','description'])
    if not os.path.exists(BUDGET_FILE):
        with open(BUDGET_FILE,'w',newline='',encoding='utf-8') as f: csv.writer(f).writerow(['category','amount'])
setup()

def txns():
    with open(TRANSACTION_FILE,encoding='utf-8') as f:
        rows=list(csv.DictReader(f))
    for r in rows:
        try:r['amount']=float(r['amount'])
        except:r['amount']=0
    return rows

def totals():
    t=txns(); income=sum(x['amount'] for x in t if x['type']=='income'); expense=sum(x['amount'] for x in t if x['type']=='expense'); return income,expense,income-expense

def cats():
    out={}
    for x in txns():
        if x['type']=='expense':out[x['category']]=out.get(x['category'],0)+x['amount']
    return out

def budgets():
    with open(BUDGET_FILE,encoding='utf-8') as f:return {r['category']:float(r['amount']) for r in csv.DictReader(f)}

def save_budgets(b):
    with open(BUDGET_FILE,'w',newline='',encoding='utf-8') as f:
        w=csv.writer(f);w.writerow(['category','amount']);w.writerows(b.items())

def health():
    i,e,b=totals()
    if i<=0:return 0,'Add some income to see your score.'
    s=50+(15 if b>0 else 0)+(15 if e<=i*.8 else 0)+(10 if b>=i*.2 else 0)+(10 if b>=i*.4 else 0)
    s=min(s,100)
    msg='Nice! Your numbers look fairly comfortable.' if s>=80 else ('Good start. Try keeping a little more aside.' if s>=60 else 'Try checking your bigger expenses and keeping a small buffer.')
    return s,msg

@app.template_filter('money')
def money(v):return f'₹{float(v):,.2f}'

@app.route('/')
def home():
    i,e,b=totals(); c=cats(); alerts=[]
    for k,limit in budgets().items():
        p=c.get(k,0)/limit*100 if limit else 0
        if p>=100:alerts.append(f'{k}: budget crossed.')
        elif p>=80:alerts.append(f'{k}: you are close to the budget.')
    s,h=health();return render_template('dashboard.html',income=i,expenses=e,balance=b,transactions=txns(),categories=c,alerts=alerts,score=s,health_text=h)

@app.route('/add',methods=['GET','POST'])
def add():
    if request.method=='POST':
        amount=float(request.form.get('amount',0))
        if amount>0:
            with open(TRANSACTION_FILE,'a',newline='',encoding='utf-8') as f:
                csv.writer(f).writerow([int(datetime.now().timestamp()*1000),request.form.get('date') or datetime.now().strftime('%Y-%m-%d'),request.form.get('type','expense'),request.form.get('category') or 'Other',amount,request.form.get('description') or ''])
        return redirect(url_for('home'))
    return render_template('add.html')

@app.route('/transactions')
def transactions():
    rows=txns();q=request.args.get('search','').lower().strip()
    if q:rows=[x for x in rows if q in x['category'].lower() or q in x['description'].lower() or q in x['type'].lower()]
    return render_template('transactions.html',transactions=rows)

@app.route('/delete/<tid>')
def delete(tid):
    rows=[x for x in txns() if str(x['id'])!=str(tid)]
    with open(TRANSACTION_FILE,'w',newline='',encoding='utf-8') as f:
        w=csv.writer(f);w.writerow(['id','date','type','category','amount','description']);w.writerows([[x['id'],x['date'],x['type'],x['category'],x['amount'],x['description']] for x in rows])
    return redirect(url_for('transactions'))

@app.route('/budget',methods=['GET','POST'])
def budget():
    b=budgets()
    if request.method=='POST':
        k=request.form.get('category','').strip();v=float(request.form.get('amount',0))
        if k and v>0:b[k]=v;save_budgets(b)
        return redirect(url_for('budget'))
    c=cats();rows=[{'category':k,'limit':v,'spent':c.get(k,0),'percent':round(c.get(k,0)/v*100,1) if v else 0} for k,v in b.items()]
    return render_template('budget.html',budgets=rows)

@app.route('/what-if',methods=['GET','POST'])
def what_if():
    i,e,b=totals();r=None
    if request.method=='POST':
        ni=i+float(request.form.get('income_change',0));ne=e+float(request.form.get('expense_change',0))+float(request.form.get('emergency',0));nb=ni-ne
        r={'income':ni,'expenses':ne,'balance':nb,'advice':'This creates a negative balance. Try reducing optional spending.' if nb<0 else ('Your safety margin would be small.' if nb<i*.1 else 'Your balance stays positive.')}
    return render_template('what_if.html',income=i,expenses=e,balance=b,result=r)

@app.route('/student-mode',methods=['GET','POST'])
def student():
    r=None
    if request.method=='POST':
        a=float(request.form.get('allowance',0));vals=[float(request.form.get(x,0)) for x in ['food','transport','education','phone','other']];g=float(request.form.get('goal',0));e=sum(vals);left=a-e
        r={'expenses':e,'left':left,'percent':round(left/a*100,1) if a else 0,'message':'Your spending is above your allowance.' if left<0 else ('Your plan can cover your savings goal.' if g and left>=g else 'You have some money left; keeping a small buffer may help.')}
    return render_template('student.html',result=r)

@app.route('/afford',methods=['GET','POST'])
def afford():
    _,_,b=totals();r=None
    if request.method=='POST':
        p=float(request.form.get('price',0));g=float(request.form.get('goal',0));after=b-p
        r={'after':after,'status':'Not a good idea right now' if after<0 else ('Think about it' if g and after<g else 'Looks manageable'),'message':'This would take your balance below zero.' if after<0 else ('It reduces money for your goal.' if g and after<g else 'This fits inside your current balance.')}
    return render_template('afford.html',balance=b,result=r)

@app.route('/savings-goal',methods=['GET','POST'])
def savings():
    r=None
    if request.method=='POST':
        target=float(request.form.get('target',0));current=float(request.form.get('current',0));months=max(int(request.form.get('months',1)),1);left=max(target-current,0);r={'left':left,'months':months,'monthly':left/months}
    return render_template('savings.html',result=r)

@app.route('/emergency-buffer',methods=['GET','POST'])
def emergency():
    r=None
    if request.method=='POST':
        a=float(request.form.get('available',0));e=float(request.form.get('essential',0));m=a/e if e else 0;r={'months':round(m,2),'message':'Good buffer.' if m>=3 else ('Some coverage, but a bigger buffer could help.' if m>=1 else 'Your current buffer is small.')}
    return render_template('emergency.html',result=r)

@app.route('/health')
def health_page():
    s,h=health();i,e,b=totals();return render_template('health.html',score=s,text=h,income=i,expenses=e,balance=b)

@app.route('/education')
def education():
    lessons=[('Needs vs Wants','Needs are usually necessary. Wants can often be delayed.'),('Budgeting','A budget helps you decide where your money should go.'),('Emergency Buffer','Money kept aside can help with unexpected costs.'),('Saving','Small regular saving can help with future goals.'),('Compound Interest','Over time, returns can also earn returns.')]
    return render_template('education.html',lessons=lessons)

@app.route('/community')
def community():return render_template('community.html')

@app.route('/demo')
def demo():
    n=int(datetime.now().timestamp()*1000);d=datetime.now().strftime('%Y-%m-%d');rows=[[n,d,'income','Allowance',5000,'Monthly allowance'],[n+1,d,'expense','Food',900,'Food and snacks'],[n+2,d,'expense','Transport',600,'Bus and travel'],[n+3,d,'expense','Education',500,'Books'],[n+4,d,'expense','Phone',300,'Recharge']]
    with open(TRANSACTION_FILE,'a',newline='',encoding='utf-8') as f:csv.writer(f).writerows(rows)
    return redirect(url_for('home'))

@app.route('/reset')
def reset():
    with open(TRANSACTION_FILE,'w',newline='',encoding='utf-8') as f:csv.writer(f).writerow(['id','date','type','category','amount','description'])
    with open(BUDGET_FILE,'w',newline='',encoding='utf-8') as f:csv.writer(f).writerow(['category','amount'])
    return redirect(url_for('home'))

@app.route('/report')
def report():
    i,e,b=totals();s,h=health();text=f'NEXUS STUDENT REPORT\n\nIncome: ₹{i:.2f}\nExpenses: ₹{e:.2f}\nBalance: ₹{b:.2f}\nHealth: {s}/100\n\nTransactions\n'
    for x in txns():text+=f"{x['date']} | {x['type']} | {x['category']} | ₹{x['amount']:.2f} | {x['description']}\n"
    f=BytesIO(text.encode());f.seek(0);return send_file(f,as_attachment=True,download_name='nexus_report.txt',mimetype='text/plain')

if __name__=='__main__':
    print('Nexus: http://127.0.0.1:5000')
    app.run(debug=True)
