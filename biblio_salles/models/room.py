from odoo import api, fields, models


class BiblioRoom(models.Model):
    _name = 'biblio.room'
    _description = 'Salle de travail'
    _order = 'name'

    name = fields.Char('Salle', required=True)
    seats = fields.Integer('Places')
    daily_price = fields.Float('Prix par jour', required=True)
    booking_ids = fields.One2many('biblio.room.booking', 'room_id', string='Réservations')
    booking_count = fields.Integer('Réservations', compute='_compute_booking_count')

    @api.depends('booking_ids')
    def _compute_booking_count(self):
        for room in self:
            room.booking_count = len(room.booking_ids)

    def action_view_bookings(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id(
            'biblio_salles.biblio_room_booking_action'
        )
        action['domain'] = [('room_id', '=', self.id)]
        action['context'] = {'default_room_id': self.id}
        return action


class BiblioRoomBooking(models.Model):
    _name = 'biblio.room.booking'
    _description = "Réservation d'une salle"
    _order = 'start_date desc'

    room_id = fields.Many2one('biblio.room', string='Salle', required=True)
    customer = fields.Char('Réservé par', required=True)
    start_date = fields.Date('Début', required=True, default=fields.Date.context_today)
    end_date = fields.Date('Fin', required=True)
    deposit = fields.Float('Caution')
    daily_price = fields.Float('Prix par jour', related='room_id.daily_price')
    duration = fields.Integer('Durée (jours)', compute='_compute_duration')
    total_price = fields.Float('Prix total', compute='_compute_total_price', store=True)

    @api.depends('start_date', 'end_date')
    def _compute_duration(self):
        for booking in self:
            booking.duration = 0
            if booking.start_date and booking.end_date:
                booking.duration = max((booking.end_date - booking.start_date).days + 1, 0)

    @api.depends('duration', 'daily_price')
    def _compute_total_price(self):
        for booking in self:
            booking.total_price = booking.duration * booking.daily_price

    @api.depends('room_id.name', 'start_date')
    def _compute_display_name(self):
        for booking in self:
            name = 'Réservation'
            if booking.room_id.name:
                name = f'{name} {booking.room_id.name}'
            if booking.start_date:
                name = f"{name} – {booking.start_date:%d/%m/%Y}"
            booking.display_name = name

    @api.onchange('room_id')
    def _onchange_room_id(self):
        self.deposit = 2 * self.room_id.daily_price if self.room_id else 0.0
