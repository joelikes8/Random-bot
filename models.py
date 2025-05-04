from app import db
from datetime import datetime
from flask_login import UserMixin

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    discord_id = db.Column(db.String(20), unique=True, nullable=False)
    roblox_id = db.Column(db.String(20), unique=True, nullable=True)
    roblox_username = db.Column(db.String(100), nullable=True)
    verification_code = db.Column(db.String(10), nullable=True)
    verified = db.Column(db.Boolean, default=False)
    verification_date = db.Column(db.DateTime, nullable=True)
    
    def __repr__(self):
        return f"<User discord_id={self.discord_id} roblox_username={self.roblox_username} verified={self.verified}>"

class ServerConfig(db.Model):
    __tablename__ = 'server_configs'
    
    id = db.Column(db.Integer, primary_key=True)
    guild_id = db.Column(db.String(20), unique=True, nullable=False)
    verified_role_id = db.Column(db.String(20), nullable=True)
    announcement_channel_id = db.Column(db.String(20), nullable=True)
    ticket_channel_id = db.Column(db.String(20), nullable=True)
    host_channel_id = db.Column(db.String(20), nullable=True)
    
    def __repr__(self):
        return f"<ServerConfig guild_id={self.guild_id}>"

class Ticket(db.Model):
    __tablename__ = 'tickets'
    
    id = db.Column(db.Integer, primary_key=True)
    guild_id = db.Column(db.String(20), nullable=False)
    channel_id = db.Column(db.String(20), unique=True, nullable=True)
    user_id = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), default="open")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    closed_at = db.Column(db.DateTime, nullable=True)
    
    def __repr__(self):
        return f"<Ticket id={self.id} user_id={self.user_id} status={self.status}>"

class TicketRole(db.Model):
    __tablename__ = 'ticket_roles'
    
    id = db.Column(db.Integer, primary_key=True)
    guild_id = db.Column(db.String(20), nullable=False)
    role_id = db.Column(db.String(20), nullable=False)
    # Whether this role is the verified role
    is_verified_role = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f"<TicketRole id={self.id} role_id={self.role_id} is_verified_role={self.is_verified_role}>"

class HostedEvent(db.Model):
    __tablename__ = 'hosted_events'
    
    id = db.Column(db.Integer, primary_key=True)
    guild_id = db.Column(db.String(20), nullable=False)
    host_id = db.Column(db.String(20), nullable=False)
    event_type = db.Column(db.String(100), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    message_id = db.Column(db.String(20), nullable=True)
    channel_id = db.Column(db.String(20), nullable=False)
    
    def __repr__(self):
        return f"<HostedEvent id={self.id} event_type={self.event_type}>"
