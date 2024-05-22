const CHECK_TYPE_REQUEST_URL = "request_url";
const STATUS_SUCCEEDED = "succeeded";
const STATUS_FAILED    = "failed";

let currentTimestampInSecs;

async function main() {
    currentTimestampInSecs = Math.ceil(Date.now()/1000);
    const res   = await fetch(`/checks?start=0&end=${currentTimestampInSecs}`);
    const items = await res.json();

    const aggregates = {};
    for (const item of items) {
        const t = item.timestamp;
        for (const check of item.checks) {
            let id, y, status;
            switch (check.type) {
                case CHECK_TYPE_REQUEST_URL:
                    id = `${check.url} -- Requests`;
                    y  = check.response_time_in_secs;
                    break;
            }
            if (typeof aggregates[id] === "undefined") {
                aggregates[id] = {
                    ts: [t],
                    ys: [y],
                    statuses: [check.status],
                };
            } else {
                aggregates[id].ts.push(t);
                aggregates[id].ys.push(y);
                aggregates[id].statuses.push(check.status);
            }
        }
    }

    const mainEl = document.getElementsByTagName("main")[0];
    for (const [id, aggregate] of Object.entries(aggregates)) {
        const el = document.createElement("div");
        el.appendChild(document.createTextNode(id));
        const lastStatus = aggregate.statuses[aggregate.statuses.length - 1];
        el.appendChild(document.createTextNode(
            ` -- Last ${lastStatus}`));
        el.appendChild(document.createElement("br"));

        const canvasEl = document.createElement("canvas");
        canvasEl.style.width  = `${mainEl.clientWidth}px`;
        canvasEl.style.height = "64px";
        el.appendChild(canvasEl);

        el.appendChild(document.createElement("br"));
        el.appendChild(document.createElement("br"));

        mainEl.appendChild(el);

        renderTimeSeriesCanvas(aggregate, canvasEl);
    }
}

function renderTimeSeriesCanvas({ts, ys, statuses}, canvasEl) {
    canvasEl.width = canvasEl.clientWidth;
    canvasEl.height = canvasEl.clientHeight;

    let tMin = ts[0];
    let tMax = currentTimestampInSecs;
    let tMinMaxDiff = tMax - tMin;
    tMin -= 0.1*tMinMaxDiff;
    tMax += 0.1*tMinMaxDiff;
    const pxPerSec = canvasEl.width/(tMax - tMin);
    const maxY = Math.max(...ys);

    const ctx = canvasEl.getContext("2d");

    // Fill background
    ctx.fillStyle = "#222";
    ctx.fillRect(0, 0, canvasEl.width, canvasEl.height);

    // Draw "pins" for timeseries values
    for (let i = 0; i < ts.length; ++i) {
        const t = ts[i];
        const y = ys[i];
        const status = statuses[i];

        const pinTopRadius = 4;
        const pinX         = (t - tMin)*pxPerSec;
        const pinTop       =
            ((maxY - y)/maxY)*(canvasEl.height - 2*pinTopRadius) + pinTopRadius;
        const pinBottom    = canvasEl.height;
        const pinColor     = status === STATUS_FAILED ? "#F00" : "#0FF";

        ctx.lineWidth = 2;
        ctx.strokeStyle = pinColor;
        ctx.beginPath();
        ctx.moveTo(pinX, pinBottom);
        ctx.lineTo(pinX, pinTop);
        ctx.stroke();

        ctx.fillStyle = pinColor;
        ctx.beginPath();
        ctx.arc(pinX, pinTop, pinTopRadius, 0, 360, 0);
        ctx.fill();
    }
}

main();

