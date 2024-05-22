const CHECK_TYPE_REQUEST_URL = "request_url";

async function main() {
    const res   = await fetch(`/checks?start=0&end=${Math.ceil(Date.now()/1000)}`);
    const items = await res.json();

    const aggregate = {};
    for (const item of items) {
        const t = item.timestamp;
        for (const check of item.checks) {
            let id, y;
            switch (check.type) {
                case CHECK_TYPE_REQUEST_URL:
                    id = `${check.url} -- Requests`;
                    y  = check.response_time_in_secs;
                    break;
            }
            if (typeof aggregate[id] === "undefined") {
                aggregate[id] = {
                    ts: [t],
                    ys: [y],
                    most_recent_t: t,
                    most_recent_status: check.status,
                };
            } else {
                aggregate[id].ts.push(t);
                aggregate[id].ys.push(y);
                aggregate[id].most_recent_t      = t;
                aggregate[id].most_recent_status = check.status;
            }
        }
    }
    console.log(aggregate);
}

main();

