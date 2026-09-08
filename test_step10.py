import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from app.models.product import Product
from app.models.warehouse import Warehouse
from app.models.stock import StockBalance, StockMovement, MovementType
from app.models.order import OrderItem
import httpx

async def run_test():
    engine = create_async_engine('sqlite+aiosqlite:///./saodat_erp.db')
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    
    async with async_session() as db:
        # 1. Create or fetch a product
        p_result = await db.execute(select(Product).where(Product.sku == 'TEST-100'))
        p = p_result.scalar_one_or_none()
        if not p:
            p = Product(sku='TEST-100', title='New Product (Test 10)', cost_price=50000, retail_price=150000, min_stock_threshold=20)
            db.add(p)
            await db.commit()
            await db.refresh(p)
        print(f'1. Product: {p.title} (ID={p.id})')
        
        # Warehouses
        w_main = (await db.execute(select(Warehouse).where(Warehouse.id == 1))).scalar_one()
        w_ucht = (await db.execute(select(Warehouse).where(Warehouse.id == 2))).scalar_one()
        
        # 2. Add 200 units to main warehouse (if not exists)
        bal_result = await db.execute(select(StockBalance).where(StockBalance.warehouse_id == w_main.id, StockBalance.product_id == p.id))
        bal = bal_result.scalar_one_or_none()
        if not bal:
            bal = StockBalance(warehouse_id=w_main.id, product_id=p.id, quantity=200)
            db.add(bal)
            db.add(StockMovement(warehouse_id=w_main.id, product_id=p.id, movement_type=MovementType.RECEIPT, quantity=200, notes='Receipt 200 units'))
            await db.commit()
            print(f'2. Added 200 units to warehouse: {w_main.name}')
        else:
            print(f'2. Balance already exists in warehouse: {w_main.name} (Qty: {bal.quantity})')

        
        product_id = p.id
    
    import requests
    
    # 3. Transfer 40 to Uchtepa via API
    print('3. Transferring 40 units to Uchtepa via API...')
    res = requests.post('http://localhost:8000/api/inventory/transfer', json={
        'product_id': product_id,
        'from_warehouse_id': 1,
        'to_warehouse_id': 2,
        'quantity': 40
    })
    if res.status_code != 200:
        print('   Error:', res.status_code, res.text)
    else:
        print('   Transfer result:', res.json())
    
    # 4. Create Order via API
    print('4. Creating order via API...')
    order_payload = {
        'customer_id': 1,
        'dispatch_warehouse_id': 2,
        'items': [{'product_id': product_id, 'quantity': 5, 'unit_price': 150000}],
        'district': 'Test District',
        'delivery_address': 'Test Address',
        'mark_paid': False
    }
    res = requests.post('http://localhost:8000/api/orders', json=order_payload)
    if res.status_code not in (200, 201):
        print('   Error:', res.status_code, res.text)
    else:
        order_data = res.json()
        order_id = order_data['id']
        print(f'   Created Order #{order_id}. Status: {order_data.get("status")}')
        
        # 5. Patch status to DELIVERED and PAID
        print('5. Progressing order statuses to DELIVERED + PAID...')
        requests.patch(f'http://localhost:8000/api/orders/{order_id}/status', json={'status': 'PACKED'})
        requests.patch(f'http://localhost:8000/api/orders/{order_id}/status', json={'status': 'DELIVERING'})
        res = requests.patch(f'http://localhost:8000/api/orders/{order_id}/status', json={'status': 'DELIVERED', 'payment_status': 'PAID'})
        final_order = res.json()
        print(f'   Final status: {final_order.get("status")}, Payment: {final_order.get("payment_status")}, Amount Paid: {final_order.get("amount_paid")}')

        
    print('SUCCESS: E2E Test completed!')

if __name__ == '__main__':
    asyncio.run(run_test())
