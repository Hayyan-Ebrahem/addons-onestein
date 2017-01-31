# -*- coding: utf-8 -*-
# Copyright 2017 Onestein (<http://www.onestein.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.addons.account.tests.account_test_classes import AccountingTestCase
from odoo.exceptions import Warning


class TestAccountCostSpread(AccountingTestCase):

    def setUp(self):
        super(TestAccountCostSpread, self).setUp()
        receivable = self.env.ref('account.data_account_type_receivable')
        expenses = self.env.ref('account.data_account_type_expenses')

        def get_account(obj):
            res = self.env['account.account'].search([
                ('user_type_id', '=', obj.id)
            ], limit=1).id
            return res

        self.invoice_account = get_account(receivable)
        self.invoice_line_account = get_account(expenses)

        self.spread_account = self.env['account.account'].search([
            ('user_type_id', '=', expenses.id),
            ('id', '!=', self.invoice_line_account.id)
        ], limit=1).id

        self.vendor = self.env['res.partner'].create({
            'name': 'Vendor1',
            'supplier': True,
        })
        self.invoice = self.env['account.invoice'].create({
            'partner_id': self.vendor.id,
            'account_id': self.invoice_account.id,
            'type': 'in_invoice',
        })
        self.invoice_line = self.env['account.invoice.line'].create({
            'quantity': 1.0,
            'price_unit': 1000.0,
            'invoice_id': self.invoice.id,
            'name': 'product that cost 1000',
            'account_id': self.invoice_line_account.id,
            'spread_account_id': self.spread_account,
            'period_number': 12,
            'period_type': 'month',
            'spread_date': '2017-02-01'
        })

    def test_01_supplier_invoice(self):
        # spread date set
        self.invoice_line.write({
            'period_number': 12,
            'period_type': 'month',
            'spread_date': '2017-02-01'
        })

        # change the state of invoice to open by clicking Validate button
        self.invoice.action_invoice_open()
        self.assertEqual(len(self.invoice_line.spread_line_ids), 12)
        self.assertEqual(81.77, self.invoice_line.spread_line_ids[0].amount)
        self.assertEqual(83.33, self.invoice_line.spread_line_ids[1].amount)
        self.assertEqual(83.33, self.invoice_line.spread_line_ids[2].amount)
        self.assertEqual(83.33, self.invoice_line.spread_line_ids[3].amount)
        self.assertEqual(83.33, self.invoice_line.spread_line_ids[4].amount)
        self.assertEqual(83.33, self.invoice_line.spread_line_ids[5].amount)
        self.assertEqual(83.33, self.invoice_line.spread_line_ids[6].amount)
        self.assertEqual(83.33, self.invoice_line.spread_line_ids[7].amount)
        self.assertEqual(83.33, self.invoice_line.spread_line_ids[8].amount)
        self.assertEqual(83.33, self.invoice_line.spread_line_ids[9].amount)
        self.assertEqual(83.33, self.invoice_line.spread_line_ids[10].amount)
        self.assertEqual(84.93, self.invoice_line.spread_line_ids[11].amount)

        # Cancel the account move which is in posted state
        # and verifies that it gives warning message
        with self.assertRaises(Warning):
            self.invoice.move_id.button_cancel()

        # create moves for all the spread lines and open them
            self.invoice_line.spread_line_ids.create_moves()

        for spread_line in self.invoice_line.spread_line_ids:
            for move_line in spread_line.move_id.line_ids:
                spread_account = self.invoice_line.spread_account_id
                if move_line.account_id == spread_account:
                    self.assertEqual(move_line.credit, spread_line.amount)

    def test_02_supplier_invoice(self):
        # date invoice set
        self.invoice.date_invoice = '2017-03-01'
        self.invoice_line.write({
            'price_unit': 2000.0,
            'name': 'product that cost 2000',
            'period_number': 7,
            'period_type': 'quarter',
            'spread_date': None
        })

        # change the state of invoice to open by clicking Validate button
        self.invoice.action_invoice_open()

        self.assertEqual(len(self.invoice_line.spread_line_ids), 8)
        self.assertEqual(100.96, self.invoice_line.spread_line_ids[0].amount)
        self.assertEqual(285.72, self.invoice_line.spread_line_ids[1].amount)
        self.assertEqual(285.72, self.invoice_line.spread_line_ids[2].amount)
        self.assertEqual(285.72, self.invoice_line.spread_line_ids[3].amount)
        self.assertEqual(285.72, self.invoice_line.spread_line_ids[4].amount)
        self.assertEqual(285.72, self.invoice_line.spread_line_ids[5].amount)
        self.assertEqual(285.72, self.invoice_line.spread_line_ids[6].amount)
        self.assertEqual(184.72, self.invoice_line.spread_line_ids[7].amount)
        total_line_amount = 0.0
        for line in self.invoice_line.spread_line_ids:
            total_line_amount += line.amount
        self.assertLessEqual(abs(total_line_amount - 2000.0), 0.0001)

        # simulate the click on the arrow that displays the spead details
        details = self.invoice_line.spread_details()
        self.assertEqual(details['res_id'], self.invoice_line.id)

    def test_03_supplier_invoice(self):
        # no date set
        self.invoice_line.write({
            'quantity': 1.0,
            'price_unit': 1000.0,
            'invoice_id': self.invoice.id,
            'name': 'product that cost 1000',
            'account_id': self.invoice_line_account.id,
            'spread_account_id': self.spread_account,
            'period_number': 3,
            'period_type': 'year',
            'spread_date': None
        })

        # change the state of invoice to open by clicking Validate button
        self.invoice.action_invoice_open()

        self.assertEqual(len(self.invoice_line.spread_line_ids), 4)
        self.assertEqual(333.33, self.invoice_line.spread_line_ids[1].amount)
        self.assertEqual(333.33, self.invoice_line.spread_line_ids[2].amount)
        first_amount = self.invoice_line.spread_line_ids[0].amount
        last_amount = self.invoice_line.spread_line_ids[3].amount
        self.assertEqual(333.34, first_amount + last_amount)
        total_line_amount = 0.0
        for line in self.invoice_line.spread_line_ids:
            total_line_amount += line.amount
        self.assertLessEqual(abs(total_line_amount - 1000.0), 0.0001)
