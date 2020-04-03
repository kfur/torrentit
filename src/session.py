
import libtorrent as lt


class SessionManager:

    def __init__(self):
        self.sessions = {}

    def new_session(self, session_id):
        print('new session ', session_id)
        session = lt.session()
        self.sessions[session_id] = session
        _setup_session(session)
        return session

    def get_session(self, session_id):
        return self.sessions.get(session_id, None)

    def del_session(self, session_id):
        print('del session ', session_id)
        del self.sessions[session_id]


def _setup_session(session):
    ses_settings = session.get_settings()
    ses_settings['cache_size'] = 1024
    ses_settings['active_downloads'] = 40

    # ses_settings['alert_mask'] = lt.alert.category_t.torrent_log_notification | lt.alert.category_t.peer_log_notification

    ses_settings['close_redundant_connections'] = False
    ses_settings['prioritize_partial_pieces'] = True
    ses_settings['support_share_mode'] = False
    session.apply_settings(ses_settings)

    session.add_dht_router("router.utorrent.com", 6881)
    session.add_dht_router("dht.transmissionbt.com", 6881)
    session.add_dht_router("router.bitcomet.com", 6881)
    session.add_dht_router("dht.aelitis.com", 6881)
    session.start_dht()
