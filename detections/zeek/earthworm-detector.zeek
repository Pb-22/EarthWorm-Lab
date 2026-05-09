@load base/frameworks/notice

module EarthWorm;

export {
    redef enum Notice::Type += {
        EarthWorm_Setup_Stage_Control_Sequence,
        EarthWorm_Post_Setup_Request_Stage_SOCKS_Sequence
    };
}

redef tcp_content_deliver_all_orig = T;

const setup_01_01 = /\x01\x01\x00\x00\x00\x00/;
const setup_01_02 = /\x01\x02\x00\x00\x00\x00/;
const setup_01_03 = /\x01\x03\x00\x00\x00\x00/;
const req_01_04   = /\x01\x04\x00\x00\x00\x00/;
const req_01_05   = /\x01\x05\x00\x00\x00\x00/;
const socks_pref  = /\x05\x02\x00\x01/;

global setup_seen_1: table[string] of bool &default=F;
global setup_seen_2: table[string] of bool &default=F;
global setup_alerted: table[string] of bool &default=F;
global req_seen_1: table[string] of bool &default=F;
global req_seen_2: table[string] of bool &default=F;
global req_alerted: table[string] of bool &default=F;

event tcp_contents(c: connection, is_orig: bool, seq: count, contents: string)
    {
    if ( ! is_orig )
        return;

    local uid = c$uid;

    if ( contents in setup_01_01 )
        setup_seen_1[uid] = T;

    if ( setup_seen_1[uid] && contents in setup_01_02 )
        setup_seen_2[uid] = T;

    if ( setup_seen_2[uid] && contents in setup_01_03 && ! setup_alerted[uid] )
        {
        NOTICE([
            $note=EarthWorm_Setup_Stage_Control_Sequence,
            $msg=fmt("EarthWorm like setup stage control sequence on %s -> %s uid=%s", c$id$orig_h, c$id$resp_h, uid),
            $conn=c,
            $identifier=cat("ew-setup|", uid)
        ]);
        setup_alerted[uid] = T;
        }

    if ( contents in req_01_04 )
        req_seen_1[uid] = T;

    if ( req_seen_1[uid] && contents in req_01_05 )
        req_seen_2[uid] = T;

    if ( req_seen_2[uid] && contents in socks_pref && ! req_alerted[uid] )
        {
        NOTICE([
            $note=EarthWorm_Post_Setup_Request_Stage_SOCKS_Sequence,
            $msg=fmt("EarthWorm like post setup request stage SOCKS sequence on %s -> %s uid=%s", c$id$orig_h, c$id$resp_h, uid),
            $conn=c,
            $identifier=cat("ew-request|", uid)
        ]);
        req_alerted[uid] = T;
        }
    }

event connection_state_remove(c: connection)
    {
    local uid = c$uid;
    delete setup_seen_1[uid];
    delete setup_seen_2[uid];
    delete setup_alerted[uid];
    delete req_seen_1[uid];
    delete req_seen_2[uid];
    delete req_alerted[uid];
    }
