const CHECK_TYPE_REQUEST_URL = "request_url";
const STATUS_SUCCEEDED = "succeeded";
const STATUS_FAILED    = "failed";

let timeWindowInSecs   = 60*60*24*5;
let pollIntervalInSecs = 10;
let currentTimestampInSecs;
let aggregateChecks;
let canvasStateByChecksAggreateId = new Map();

async function main() {
    update();
    setInterval(update, pollIntervalInSecs*1000);

    window.addEventListener("resize", () => renderAggregateChecks(aggregateChecks));
}

async function update() {
    currentTimestampInSecs = Math.ceil(Date.now()/1000);
    const res   = await fetch(
        `/checks?start=${currentTimestampInSecs - timeWindowInSecs}` +
        `&end=${currentTimestampInSecs}`);
    const items = await res.json();

    const aggregates = {};
    for (const item of items) {
        const t = item.timestamp;
        for (const check of item.checks) {
            let id, y, status;
            switch (check.type) {
                case CHECK_TYPE_REQUEST_URL:
                    id = `${check.url} — Requests`;
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

    canvasIdx = 0;

    renderAggregateChecks(aggregates);

    aggregateChecks = aggregates;
}

function renderAggregateChecks(aggregates) {
    const checksEl = document.getElementById("checks");
    checksEl.innerHTML = "";

    for (const [id, aggregate] of Object.entries(aggregates)) {
        const el = document.createElement("div");
        // Status line and description
        {
            const statusAndDescriptionLineEl = document.createElement("div");
            statusAndDescriptionLineEl.classList.add("status-and-description-line");

            const lastStatus = aggregate.statuses[aggregate.statuses.length - 1];

            const statusPill = document.createElement("span");
            statusPill.classList.add("status-pill");
            if (lastStatus === STATUS_SUCCEEDED) {
                statusPill.classList.add("status-pill--succeeded");
            } else {
                statusPill.classList.add("status-pill--failed");
            }
            statusPill.appendChild(document.createTextNode(`Last ${lastStatus}`));
            statusAndDescriptionLineEl.appendChild(statusPill);

            statusAndDescriptionLineEl.appendChild(document.createTextNode(id));
            statusAndDescriptionLineEl.appendChild(document.createElement("br"));
            el.appendChild(statusAndDescriptionLineEl);
        }

        // Timeseries canvas
        const canvasEl = document.createElement("canvas");
        canvasEl.style.width  = `${checksEl.clientWidth}px`;
        canvasEl.style.height = "64px";
        canvasEl.setAttribute("id", `Canvas for ${id}`);
        el.appendChild(canvasEl);

        el.appendChild(document.createElement("br"));

        // Timeseries "scrub" head
        const srubHeadDatetimeEl = document.createElement("span");
        srubHeadDatetimeEl.appendChild(document.createTextNode(
            dateFromTimestamp(currentTimestampInSecs).toLocaleString()
        ));
        el.appendChild(srubHeadDatetimeEl);

        el.appendChild(document.createElement("br"));
        el.appendChild(document.createElement("br"));

        // -----------------------------------------------------------

        checksEl.appendChild(el);

        const ctx = canvasEl.getContext("2d");
        renderTimeSeriesCanvas(aggregate, ctx, canvasEl);

        canvasEl.addEventListener("mousemove", function moveScrubHead(event) {
            const canvasState = getCanvasState(aggregate.id);

            canvasState.tScrubHead =
                (event.offsetX/canvasEl.clientWidth)
                *(canvasState.tMax - canvasState.tMin)
                + canvasState.tMin;
            srubHeadDatetimeEl.innerHTML = "";

            srubHeadDatetimeEl.appendChild(document.createTextNode(
                dateFromTimestamp(canvasState.tScrubHead).toLocaleString()
            ));

            renderTimeSeriesCanvas(aggregate, ctx, canvasEl);
        });
    }
}

function renderTimeSeriesCanvas(aggregate, ctx, canvasEl) {
    const {id, ts, ys, statuses} = aggregate;

    const canvasState = getCanvasState(id);

    canvasEl.width  = canvasEl.clientWidth;
    canvasEl.height = canvasEl.clientHeight;

    let tMin = ts[0];
    let tMax = currentTimestampInSecs;
    const pxPerSec = canvasEl.width/(tMax - tMin);
    const maxY = Math.max(...ys);
    canvasState.tMin = tMin;
    canvasState.tMax = tMax;

    function drawVerticalLine(t, height) {
        const x = (t - tMin)*pxPerSec;

        ctx.beginPath();
        ctx.moveTo(x, canvasEl.height);
        ctx.lineTo(x, canvasEl.height - height);
        ctx.stroke();
    }

    // Fill background
    ctx.fillStyle = "#222";
    ctx.fillRect(0, 0, canvasEl.width, canvasEl.height);

    // Draw day, 6 hour and 1 hour rules
    let day = new Date();
    day.setTime(tMax*1000);
    day.setDate(day.getDate() + 1);
    day.setHours(0);
    day.setMinutes(0);
    day.setSeconds(0);
    day.setMilliseconds(0);
    while (day.getTime()/1000 > tMin) {
        ctx.lineWidth = 2;
        ctx.strokeStyle = "#000";
        drawVerticalLine(day.getTime()/1000, canvasEl.height);
        day = new Date(day);
        day.setDate(day.getDate() - 1);
    }
    let hour = new Date();
    hour.setTime(tMax*1000);
    hour.setHours(hour.getHours() + (6 - hour.getHours()%6));
    hour.setMinutes(0);
    hour.setSeconds(0);
    hour.setMilliseconds(0);
    while (hour.getTime()/1000 > tMin) {
        ctx.lineWidth = 1;
        ctx.strokeStyle = "#000";
        ctx.setLineDash([6, 2]);
        ctx.beginPath();
        drawVerticalLine(hour.getTime()/1000, canvasEl.height);
        hour = new Date(hour);
        hour.setHours(hour.getHours() - 6);
    }
    hour = new Date();
    hour.setTime(tMax*1000);
    hour.setHours(hour.getHours() + 1);
    hour.setMinutes(0);
    hour.setSeconds(0);
    hour.setMilliseconds(0);
    while (hour.getTime()/1000 > tMin) {
        ctx.lineWidth = 2;
        ctx.strokeStyle = "#000";
        ctx.setLineDash([2, 7]);
        drawVerticalLine(hour.getTime()/1000, canvasEl.height);
        hour = new Date(hour);
        hour.setHours(hour.getHours() - 1);
    }

    // Draw scrub head rule
    ctx.lineWidth = 2;
    ctx.strokeStyle = "#FFF";
    ctx.setLineDash([]);
    drawVerticalLine(canvasState.tScrubHead, canvasEl.height);

    // Draw "pins" for timeseries values.
    // Drawn in 2 passes so that the pins for failures are drawn in front of
    // those for successees.
    for (const [status_for_draw_pass, color] of [
        [STATUS_SUCCEEDED, "#F00"],
        [STATUS_FAILED   , "#0FF"],
    ]) {
        for (let i = 0; i < ts.length; ++i) {
            const status = statuses[i];
            if (status != status_for_draw_pass) continue;

            const t = ts[i];
            const y = ys[i];

            const pinTopRadius = 4;
            const pinX         = (t - tMin)*pxPerSec;
            const pinHeight    = (y/maxY)*(canvasEl.height - 2*pinTopRadius) + pinTopRadius;
            const pinColor     = status === STATUS_FAILED ? "#F00" : "#0FF";

            ctx.lineWidth = 2;
            ctx.strokeStyle = pinColor;
            ctx.setLineDash([]);
            drawVerticalLine(t, pinHeight);

            ctx.fillStyle = pinColor;
            ctx.beginPath();
            ctx.arc(pinX, canvasEl.height - pinHeight, pinTopRadius, 0, 360, 0);
            ctx.fill();
        }
    }

    canvasIdx++;
}

function getCanvasState(checksAggregateId) {
    let state = canvasStateByChecksAggreateId.get(checksAggregateId);
    if (typeof state === "undefined") {
        state = {
            tMin: -1,
            tMax: -1,
            tScrubHead: currentTimestampInSecs,
        };
        canvasStateByChecksAggreateId.set(checksAggregateId, state);
    }
    return state;
}

function dateFromTimestamp(timestamp) {
    const date = new Date();
    date.setTime(timestamp*1000);
    return date;
}

main();

