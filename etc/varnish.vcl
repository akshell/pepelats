backend default {
    .host = "127.0.0.1";
    .port = "9864";
    .connect_timeout = 100s;
    .first_byte_timeout = 100s;
    .between_bytes_timeout = 100s;
}

acl purge {
    "127.0.0.1";
}

sub vcl_recv {
    if (req.request == "PURGE") {
        if (!(client.ip ~ purge)) {
            error 405 "Not allowed.";
        }
        purge("req.http.host ~ " req.http.host);
        error 200 "Purged.";
    }
    set req.url = req.http.host "                                                                                                                                " req.request " " req.url;
    if (req.http.x-forwarded-for) {
      set req.http.X-Forwarded-For = req.http.X-Forwarded-For ", " client.ip;
    } else {
      set req.http.X-Forwarded-For = client.ip;
    }
    if (req.request != "GET" &&
        req.request != "HEAD" &&
        req.request != "PUT" &&
        req.request != "POST" &&
        req.request != "TRACE" &&
        req.request != "OPTIONS" &&
        req.request != "DELETE") {
        return (pipe);
    }
    if (req.request != "GET" && req.request != "HEAD") {
        return (pass);
    }
    return (lookup);
}

sub vcl_fetch {
    if (!beresp.cacheable ||
        beresp.http.Set-Cookie ||
        beresp.http.Vary ~ "(?i)cookie" ||
        beresp.http.Cache-Control ~ "(?i)no-cache") {
        return (pass);
    }
    return (deliver);
}
