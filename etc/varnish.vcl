backend default {
    .host = "127.0.0.1";
    .port = "9864";
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
}
