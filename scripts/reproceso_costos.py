for rec in records:
  
  if 'USD' in rec.stock_move_id.purchase_line_id.order_id.currency_id.name:
    for inv in rec.stock_move_id.purchase_line_id.order_id.invoice_ids:
      rate_op = model.env['res.currency.rate'].search(
                          # [('name', '=', rec.stock_move_id.purchase_line_id.date_order),
                          [('name', '=', inv.invoice_date),
                          ('currency_id', '=', inv.currency_id.id)])
      valor= (rec.stock_move_id.purchase_line_id.price_unit * rate_op[0].set_venta)/1.1
      cost = valor * rec.stock_move_id.quantity_done
      if rate_op:
        rec.write({'unit_cost': valor})
        rec.write({'value': cost})
        rec.write({'description': 'value' + str(cost) + 'unit_cost' + str(valor) + 'rate' + str(rate_op[0].set_venta)})
      else:
        
        valor= round(rec.stock_move_id.purchase_line_id.price_unit)/1.1
        cost = valor * rec.stock_move_id.quantity_done
        
        rec.write({'unit_cost': valor})
        rec.write({'value': cost})
        rec.write({'description': rec.stock_move_id.purchase_line_id.order_id.currency_id.name})
      
      vl=cost
      rec.write({'value':vl})
      if rec.account_move_id:
        rec.account_move_id.button_draft()
        for ml in rec.account_move_id.line_ids:
          if ml.debit>0:
            ml.with_context(check_move_validity=False).write({'debit':abs(vl)})
          elif ml.credit>0:
            ml.with_context(check_move_validity=False).write({'credit':abs(vl)})
        rec.account_move_id.action_post()
