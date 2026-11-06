rama_hieght=1.3
raja_hieght=1.7
if rama_hieght>rama_hieght:
    print('rama is taller')
else:
    print('raja is taller')
    total=float(input("enter total purchase amount:"))
if total>=1000:
    discount=total*0.10
    final_amount=total-discount
    print("discount applied:",discount)
    print("final amount to pay:",final_amount)
else:
    print("no discount applied")
    print("total amount:",total)
    
