import { app } from "/scripts/app.js";
import { api } from "/scripts/api.js";


const NODE_NAME = "EasyUrlLoader";
const PANEL_MIN_HEIGHT = 620;
const DEFAULT_SELECTION = {
    version: 1,
    full: { enabled: true, format: "bestvideo+bestaudio/best" },
    audio: { enabled: false, format: "bestaudio" },
    video: { enabled: false, format: "bestvideo" },
};

const OUTPUTS = {
    full: {
        title: "Full video",
        description: "Video with audio merged together",
        autoLabel: "Best available · video + best audio",
    },
    audio: {
        title: "Audio only",
        description: "Separate MP3 audio output",
        autoLabel: "Best available audio",
    },
    video: {
        title: "Video only",
        description: "Separate video stream without audio",
        autoLabel: "Best available video",
    },
};

const DIRECTORY_FIELDS = {
    full: {
        widget: "full_output_dir",
        title: "Full video destination",
        defaultPath: "downloads/full",
    },
    audio: {
        widget: "audio_output_dir",
        title: "Audio destination",
        defaultPath: "downloads/audio",
    },
    video: {
        widget: "video_output_dir",
        title: "Video-only destination",
        defaultPath: "downloads/video",
    },
};

const STYLE_ID = "easyurl-loader-panel-styles";
const STYLES = `
.easyurl-loader-panel {
    --easyurl-bg: #171a1f;
    --easyurl-surface: #20252d;
    --easyurl-surface-strong: #292f39;
    --easyurl-border: rgba(255, 255, 255, .11);
    --easyurl-text: #f1f5f9;
    --easyurl-muted: #9aa6b5;
    --easyurl-accent: #61d6a5;
    --easyurl-accent-dark: #1f8d68;
    box-sizing: border-box;
    width: 100%;
    min-width: 390px;
    padding: 12px;
    color: var(--easyurl-text);
    background: var(--easyurl-bg);
    border: 1px solid var(--easyurl-border);
    border-radius: 10px;
    font-family: Inter, ui-sans-serif, system-ui, sans-serif;
    font-size: 12px;
    line-height: 1.35;
}
.easyurl-loader-panel * { box-sizing: border-box; }
.easyurl-loader-panel button,
.easyurl-loader-panel select {
    font: inherit;
}
.easyurl-loader-panel button {
    cursor: pointer;
    color: var(--easyurl-text);
    background: var(--easyurl-surface-strong);
    border: 1px solid var(--easyurl-border);
    border-radius: 7px;
    transition: background .15s ease, border-color .15s ease, opacity .15s ease;
}
.easyurl-loader-panel button:hover:not(:disabled) {
    background: #343c48;
    border-color: rgba(97, 214, 165, .65);
}
.easyurl-loader-panel button:disabled,
.easyurl-loader-panel select:disabled {
    cursor: default;
    opacity: .52;
}
.easyurl-loader-panel .easyurl-header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 10px;
    margin-bottom: 10px;
}
.easyurl-loader-panel .easyurl-eyebrow {
    margin: 0 0 2px;
    color: var(--easyurl-accent);
    font-size: 10px;
    font-weight: 700;
    letter-spacing: .09em;
    text-transform: uppercase;
}
.easyurl-loader-panel h3 {
    margin: 0;
    color: var(--easyurl-text);
    font-size: 16px;
    font-weight: 700;
}
.easyurl-loader-panel .easyurl-intro {
    margin: 3px 0 0;
    color: var(--easyurl-muted);
    font-size: 11px;
}
.easyurl-loader-panel .easyurl-analyze {
    flex: 0 0 auto;
    min-height: 34px;
    padding: 0 12px;
    color: #0b2a20;
    background: var(--easyurl-accent);
    border-color: transparent;
    font-weight: 700;
}
.easyurl-loader-panel .easyurl-analyze:hover:not(:disabled) {
    background: #83e8bf;
}
.easyurl-loader-panel .easyurl-status {
    display: flex;
    align-items: center;
    min-height: 29px;
    margin-bottom: 10px;
    padding: 7px 9px;
    color: var(--easyurl-muted);
    background: rgba(255, 255, 255, .035);
    border: 1px solid transparent;
    border-radius: 7px;
}
.easyurl-loader-panel .easyurl-status[data-tone="success"] {
    color: #b5f5d8;
    background: rgba(97, 214, 165, .09);
    border-color: rgba(97, 214, 165, .22);
}
.easyurl-loader-panel .easyurl-status[data-tone="error"] {
    color: #ffb4b4;
    background: rgba(255, 90, 90, .09);
    border-color: rgba(255, 90, 90, .22);
}
.easyurl-loader-panel .easyurl-status[data-tone="loading"] {
    color: #c7d9ff;
    background: rgba(113, 153, 255, .09);
    border-color: rgba(113, 153, 255, .22);
}
.easyurl-loader-panel .easyurl-summary {
    margin-bottom: 10px;
    padding: 9px 10px;
    background: linear-gradient(135deg, rgba(97, 214, 165, .13), rgba(97, 214, 165, .025));
    border: 1px solid rgba(97, 214, 165, .22);
    border-radius: 8px;
}
.easyurl-loader-panel .easyurl-summary-title {
    overflow: hidden;
    color: var(--easyurl-text);
    font-weight: 700;
    text-overflow: ellipsis;
    white-space: nowrap;
}
.easyurl-loader-panel .easyurl-summary-meta {
    margin-top: 3px;
    color: var(--easyurl-muted);
    font-size: 11px;
}
.easyurl-loader-panel .easyurl-section-title {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    margin: 12px 0 6px;
    color: #dce5ef;
    font-size: 12px;
    font-weight: 700;
}
.easyurl-loader-panel .easyurl-section-title span {
    color: var(--easyurl-muted);
    font-size: 10px;
    font-weight: 500;
}
.easyurl-loader-panel .easyurl-choice-grid,
.easyurl-loader-panel .easyurl-folder-grid {
    display: grid;
    gap: 7px;
}
.easyurl-loader-panel .easyurl-choice-card {
    padding: 9px;
    background: var(--easyurl-surface);
    border: 1px solid var(--easyurl-border);
    border-radius: 8px;
}
.easyurl-loader-panel .easyurl-choice-card[data-enabled="true"] {
    border-color: rgba(97, 214, 165, .46);
    box-shadow: inset 3px 0 0 var(--easyurl-accent-dark);
}
.easyurl-loader-panel .easyurl-choice-top {
    display: flex;
    align-items: flex-start;
    gap: 8px;
}
.easyurl-loader-panel .easyurl-choice-top input {
    flex: 0 0 auto;
    width: 16px;
    height: 16px;
    margin: 1px 0 0;
    accent-color: var(--easyurl-accent);
}
.easyurl-loader-panel .easyurl-choice-name {
    color: var(--easyurl-text);
    font-weight: 700;
}
.easyurl-loader-panel .easyurl-choice-description {
    margin-top: 1px;
    color: var(--easyurl-muted);
    font-size: 10px;
}
.easyurl-loader-panel .easyurl-format-label {
    display: block;
    margin-top: 8px;
    color: var(--easyurl-muted);
    font-size: 10px;
    font-weight: 600;
    text-transform: uppercase;
}
.easyurl-loader-panel select {
    width: 100%;
    min-height: 31px;
    margin-top: 3px;
    padding: 0 8px;
    color: var(--easyurl-text);
    background: #15181d;
    border: 1px solid var(--easyurl-border);
    border-radius: 6px;
}
.easyurl-loader-panel .easyurl-choice-hint {
    overflow: hidden;
    min-height: 15px;
    margin-top: 4px;
    color: var(--easyurl-muted);
    font-size: 10px;
    text-overflow: ellipsis;
    white-space: nowrap;
}
.easyurl-loader-panel .easyurl-folder-card {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    padding: 8px 9px;
    background: var(--easyurl-surface);
    border: 1px solid var(--easyurl-border);
    border-radius: 8px;
}
.easyurl-loader-panel .easyurl-folder-copy {
    min-width: 0;
}
.easyurl-loader-panel .easyurl-folder-name {
    color: var(--easyurl-text);
    font-weight: 700;
}
.easyurl-loader-panel .easyurl-folder-path {
    overflow: hidden;
    margin-top: 2px;
    color: var(--easyurl-muted);
    font-size: 10px;
    text-overflow: ellipsis;
    white-space: nowrap;
}
.easyurl-loader-panel .easyurl-folder-actions {
    display: flex;
    flex: 0 0 auto;
    gap: 5px;
}
.easyurl-loader-panel .easyurl-folder-actions button {
    min-height: 29px;
    padding: 0 8px;
    font-size: 10px;
}
.easyurl-loader-panel .easyurl-folder-actions .easyurl-reset {
    color: var(--easyurl-muted);
    background: transparent;
}
.easyurl-loader-panel .easyurl-footnote {
    margin: 10px 1px 0;
    color: var(--easyurl-muted);
    font-size: 10px;
}
`;


function ensureStyles() {
    if (document.getElementById(STYLE_ID)) return;
    const style = document.createElement("style");
    style.id = STYLE_ID;
    style.textContent = STYLES;
    document.head.appendChild(style);
}


function isEasyUrlNode(node) {
    return node?.comfyClass === NODE_NAME || node?.type === NODE_NAME;
}


function findWidget(node, name) {
    return (node.widgets || []).find((widget) => widget.name === name) || null;
}


function hideWidget(widget) {
    if (!widget || widget.__easyUrlHidden) return;
    widget.__easyUrlHidden = true;
    widget.hidden = true;
    widget.computeSize = () => [0, -4];
    widget.computedHeight = 0;
    widget.type = "converted-widget";
}


function cloneDefaultSelection() {
    return JSON.parse(JSON.stringify(DEFAULT_SELECTION));
}


function parseSelection(value) {
    let parsed = {};
    try {
        parsed = typeof value === "string" ? JSON.parse(value) : value;
    } catch (_error) {
        parsed = {};
    }
    if (!parsed || typeof parsed !== "object") parsed = {};

    const selection = cloneDefaultSelection();
    for (const kind of Object.keys(OUTPUTS)) {
        if (!parsed[kind] || typeof parsed[kind] !== "object") continue;
        if (typeof parsed[kind].enabled === "boolean") {
            selection[kind].enabled = parsed[kind].enabled;
        }
        if (typeof parsed[kind].format === "string" && parsed[kind].format) {
            selection[kind].format = parsed[kind].format;
        }
    }
    return selection;
}


function setWidgetValue(node, widget, value) {
    if (!widget) return;
    widget.value = value;
    if (typeof widget.callback === "function") {
        widget.callback.call(widget, value, app.canvas, node, app.canvas?.graph_mouse, {});
    }
    if (node.graph) {
        node.graph._version++;
        node.graph.setDirtyCanvas?.(true, true);
    }
}


function likelyUrl(value) {
    const trimmed = String(value || "").trim();
    return trimmed.startsWith("http://") || trimmed.startsWith("https://") || trimmed.includes(".");
}


function compareUrl(value) {
    const trimmed = String(value || "").trim();
    if (!trimmed) return "";
    return trimmed.includes("://") ? trimmed : `https://${trimmed}`;
}


function createPanel(node, widgets) {
    ensureStyles();

    const root = document.createElement("div");
    root.className = "easyurl-loader-panel";
    root.innerHTML = `
        <div class="easyurl-header">
            <div>
                <p class="easyurl-eyebrow">Smart download options</p>
                <h3>Choose what to download</h3>
                <p class="easyurl-intro">Analyze the URL first, then choose quality for each output.</p>
            </div>
            <button class="easyurl-analyze" type="button" data-action="analyze">Analyze URL</button>
        </div>
        <div class="easyurl-status" data-role="status" data-tone="info">Enter a URL, then click Analyze URL.</div>
        <div class="easyurl-summary" data-role="summary" hidden>
            <div class="easyurl-summary-title" data-role="summary-title"></div>
            <div class="easyurl-summary-meta" data-role="summary-meta"></div>
        </div>
        <div class="easyurl-section-title">
            <span>Download types</span>
            <span>Enable one or more outputs</span>
        </div>
        <div class="easyurl-choice-grid">
            <div class="easyurl-choice-card" data-choice="full">
                <div class="easyurl-choice-top">
                    <input type="checkbox" data-role="enabled" aria-label="Enable full video download">
                    <div>
                        <div class="easyurl-choice-name">Full video</div>
                        <div class="easyurl-choice-description">Video with audio merged together</div>
                    </div>
                </div>
                <label class="easyurl-format-label">Video resolution and quality
                    <select data-role="format" aria-label="Full video quality"></select>
                </label>
                <div class="easyurl-choice-hint" data-role="hint"></div>
            </div>
            <div class="easyurl-choice-card" data-choice="audio">
                <div class="easyurl-choice-top">
                    <input type="checkbox" data-role="enabled" aria-label="Enable audio download">
                    <div>
                        <div class="easyurl-choice-name">Audio only</div>
                        <div class="easyurl-choice-description">Separate MP3 audio output</div>
                    </div>
                </div>
                <label class="easyurl-format-label">Audio quality
                    <select data-role="format" aria-label="Audio quality"></select>
                </label>
                <div class="easyurl-choice-hint" data-role="hint"></div>
            </div>
            <div class="easyurl-choice-card" data-choice="video">
                <div class="easyurl-choice-top">
                    <input type="checkbox" data-role="enabled" aria-label="Enable video-only download">
                    <div>
                        <div class="easyurl-choice-name">Video only</div>
                        <div class="easyurl-choice-description">Separate video stream without audio</div>
                    </div>
                </div>
                <label class="easyurl-format-label">Video resolution and quality
                    <select data-role="format" aria-label="Video-only quality"></select>
                </label>
                <div class="easyurl-choice-hint" data-role="hint"></div>
            </div>
        </div>
        <div class="easyurl-section-title">
            <span>Output folders</span>
            <span>Choose a folder on the ComfyUI machine</span>
        </div>
        <div class="easyurl-folder-grid">
            <div class="easyurl-folder-card" data-folder="full">
                <div class="easyurl-folder-copy">
                    <div class="easyurl-folder-name">Full video destination</div>
                    <div class="easyurl-folder-path" data-role="path" title=""></div>
                </div>
                <div class="easyurl-folder-actions">
                    <button type="button" data-action="pick">Choose folder</button>
                    <button class="easyurl-reset" type="button" data-action="reset">Default</button>
                </div>
            </div>
            <div class="easyurl-folder-card" data-folder="audio">
                <div class="easyurl-folder-copy">
                    <div class="easyurl-folder-name">Audio destination</div>
                    <div class="easyurl-folder-path" data-role="path" title=""></div>
                </div>
                <div class="easyurl-folder-actions">
                    <button type="button" data-action="pick">Choose folder</button>
                    <button class="easyurl-reset" type="button" data-action="reset">Default</button>
                </div>
            </div>
            <div class="easyurl-folder-card" data-folder="video">
                <div class="easyurl-folder-copy">
                    <div class="easyurl-folder-name">Video-only destination</div>
                    <div class="easyurl-folder-path" data-role="path" title=""></div>
                </div>
                <div class="easyurl-folder-actions">
                    <button type="button" data-action="pick">Choose folder</button>
                    <button class="easyurl-reset" type="button" data-action="reset">Default</button>
                </div>
            </div>
        </div>
        <p class="easyurl-footnote">Selections are saved with the workflow and used when you queue it. Audio is converted to MP3.</p>
    `;

    const domWidget = node.addDOMWidget("easyurl_loader_panel", "div", root, {
        serialize: false,
        hideOnZoom: false,
        getMinHeight: () => PANEL_MIN_HEIGHT,
    });
    domWidget.computeSize = () => [Math.max(node.size?.[0] || 0, 460), PANEL_MIN_HEIGHT];

    const state = {
        info: null,
        formats: { full: [], audio: [], video: [] },
        selection: parseSelection(widgets.selection?.value),
        lastUrl: "",
        loading: false,
        probeId: 0,
        probeTimer: null,
        disposed: false,
    };

    const status = root.querySelector('[data-role="status"]');
    const summary = root.querySelector('[data-role="summary"]');
    const summaryTitle = root.querySelector('[data-role="summary-title"]');
    const summaryMeta = root.querySelector('[data-role="summary-meta"]');
    const analyzeButton = root.querySelector('[data-action="analyze"]');

    function setStatus(message, tone = "info") {
        status.textContent = message;
        status.dataset.tone = tone;
    }

    function saveSelection() {
        setWidgetValue(node, widgets.selection, JSON.stringify(state.selection));
        // Keep the legacy hidden toggles synchronized so workflows created
        // before the smart panel can still be opened and saved safely.
        setWidgetValue(node, widgets.legacyFull, state.selection.full.enabled);
        setWidgetValue(node, widgets.legacyAudio, state.selection.audio.enabled);
        setWidgetValue(node, widgets.legacyVideo, state.selection.video.enabled);
    }

    function migrateLegacySelection() {
        const configured = parseSelection(widgets.selection?.value);
        const defaults = cloneDefaultSelection();
        const legacyValues = {
            full: Boolean(widgets.legacyFull?.value),
            audio: Boolean(widgets.legacyAudio?.value),
            video: Boolean(widgets.legacyVideo?.value),
        };
        const legacyDiffers =
            legacyValues.full !== defaults.full.enabled ||
            legacyValues.audio !== defaults.audio.enabled ||
            legacyValues.video !== defaults.video.enabled;
        if (JSON.stringify(configured) !== JSON.stringify(defaults) || !legacyDiffers) return false;

        state.selection = configured;
        state.selection.full.enabled = legacyValues.full;
        state.selection.audio.enabled = legacyValues.audio;
        state.selection.video.enabled = legacyValues.video;
        saveSelection();
        return true;
    }

    function selectedFormatLabel(kind) {
        const select = root.querySelector(`[data-choice="${kind}"] [data-role="format"]`);
        return select?.selectedOptions?.[0]?.textContent || "Best available";
    }

    function renderChoices() {
        let selectionChanged = false;
        for (const [kind, metadata] of Object.entries(OUTPUTS)) {
            const card = root.querySelector(`[data-choice="${kind}"]`);
            const enabledInput = card.querySelector('[data-role="enabled"]');
            const select = card.querySelector('[data-role="format"]');
            const hint = card.querySelector('[data-role="hint"]');
            const current = state.selection[kind];
            const options = [
                { format: DEFAULT_SELECTION[kind].format, label: metadata.autoLabel },
                ...(state.formats[kind] || []),
            ];
            const uniqueOptions = [];
            const seen = new Set();
            for (const option of options) {
                if (!option?.format || seen.has(option.format)) continue;
                seen.add(option.format);
                uniqueOptions.push(option);
            }

            const currentFormat = current.format;
            select.replaceChildren();
            for (const optionData of uniqueOptions) {
                const option = document.createElement("option");
                option.value = optionData.format;
                option.textContent = optionData.label || optionData.format;
                option.title = optionData.label || optionData.format;
                select.appendChild(option);
            }
            if (!uniqueOptions.some((option) => option.format === currentFormat)) {
                state.selection[kind].format = uniqueOptions[0]?.format || DEFAULT_SELECTION[kind].format;
                selectionChanged = true;
            }
            select.value = state.selection[kind].format;
            enabledInput.checked = Boolean(current.enabled);
            select.disabled = !current.enabled || state.loading;
            card.dataset.enabled = String(current.enabled);
            hint.textContent = current.enabled
                ? selectedFormatLabel(kind)
                : "Not selected — its output will stay empty.";
            hint.title = hint.textContent;
        }
        if (selectionChanged) saveSelection();
    }

    function renderSummary() {
        if (!state.info) {
            summary.hidden = true;
            return;
        }
        summary.hidden = false;
        summaryTitle.textContent = state.info.title || "Untitled";
        const details = [state.info.uploader, state.info.duration].filter(Boolean);
        summaryMeta.textContent = details.length ? details.join(" · ") : "Formats found for this URL";
    }

    function renderFolders() {
        for (const [kind, metadata] of Object.entries(DIRECTORY_FIELDS)) {
            const folderWidget = widgets[metadata.widget];
            const card = root.querySelector(`[data-folder="${kind}"]`);
            const path = String(folderWidget?.value || "").trim();
            const pathElement = card.querySelector('[data-role="path"]');
            pathElement.textContent = path || `Default: ${metadata.defaultPath}`;
            pathElement.title = path || metadata.defaultPath;
        }
    }

    function render() {
        renderSummary();
        renderChoices();
        renderFolders();
        analyzeButton.disabled = state.loading;
    }

    async function probeUrl() {
        const rawUrl = String(widgets.url?.value || "").trim();
        if (!likelyUrl(rawUrl)) {
            setStatus("Enter a complete URL before analyzing it.", "error");
            return;
        }

        const requestId = ++state.probeId;
        const urlForComparison = compareUrl(rawUrl);
        state.loading = true;
        state.info = null;
        state.formats = { full: [], audio: [], video: [] };
        state.lastUrl = urlForComparison;
        setStatus("Checking the available video, audio, and resolution choices…", "loading");
        render();

        try {
            const response = await api.fetchApi(`/easyurl/probe?url=${encodeURIComponent(rawUrl)}`);
            const payload = await response.json();
            if (requestId !== state.probeId) return;
            if (!response.ok || payload.error) {
                throw new Error(payload.error || `The URL could not be analyzed (${response.status}).`);
            }
            state.info = payload;
            state.formats = payload.formats || { full: [], audio: [], video: [] };
            state.lastUrl = compareUrl(payload.url || rawUrl);
            setStatus("Formats found. Select one or more outputs, then queue the workflow to download.", "success");
        } catch (error) {
            if (requestId !== state.probeId) return;
            state.info = null;
            state.formats = { full: [], audio: [], video: [] };
            setStatus(error?.message || "The URL could not be analyzed.", "error");
        } finally {
            if (requestId === state.probeId) {
                state.loading = false;
                render();
            }
        }
    }

    function scheduleProbe() {
        if (state.probeTimer) clearTimeout(state.probeTimer);
        const rawUrl = String(widgets.url?.value || "").trim();
        if (!likelyUrl(rawUrl)) return;
        state.probeTimer = setTimeout(() => {
            state.probeTimer = null;
            probeUrl();
        }, 650);
    }

    function handleUrlChange(value) {
        const nextUrl = compareUrl(value);
        if (nextUrl === state.lastUrl) return;
        state.probeId += 1;
        state.loading = false;
        state.lastUrl = nextUrl;
        state.info = null;
        state.formats = { full: [], audio: [], video: [] };
        state.selection = cloneDefaultSelection();
        saveSelection();
        setStatus(likelyUrl(value) ? "URL changed. Checking it shortly…" : "Enter a URL, then click Analyze URL.");
        render();
        scheduleProbe();
    }

    async function chooseFolder(kind) {
        const metadata = DIRECTORY_FIELDS[kind];
        const button = root.querySelector(`[data-folder="${kind}"] [data-action="pick"]`);
        const existingPath = String(widgets[metadata.widget]?.value || "").trim();
        button.disabled = true;
        button.textContent = "Opening…";
        try {
            const response = await api.fetchApi(
                `/easyurl/select-directory?initial=${encodeURIComponent(existingPath)}`,
            );
            const payload = await response.json();
            if (!response.ok || payload.error) {
                throw new Error(payload.error || "The folder picker could not be opened.");
            }
            if (payload.path) {
                setWidgetValue(node, widgets[metadata.widget], payload.path);
                renderFolders();
                setStatus(`${metadata.title} updated.`, "success");
            }
        } catch (error) {
            setStatus(error?.message || "The folder picker could not be opened.", "error");
        } finally {
            button.disabled = false;
            button.textContent = "Choose folder";
        }
    }

    for (const kind of Object.keys(OUTPUTS)) {
        const card = root.querySelector(`[data-choice="${kind}"]`);
        const enabledInput = card.querySelector('[data-role="enabled"]');
        const select = card.querySelector('[data-role="format"]');
        enabledInput.addEventListener("change", () => {
            state.selection[kind].enabled = enabledInput.checked;
            saveSelection();
            renderChoices();
        });
        select.addEventListener("change", () => {
            state.selection[kind].format = select.value;
            saveSelection();
            renderChoices();
        });
    }

    for (const kind of Object.keys(DIRECTORY_FIELDS)) {
        const card = root.querySelector(`[data-folder="${kind}"]`);
        card.querySelector('[data-action="pick"]').addEventListener("click", () => chooseFolder(kind));
        card.querySelector('[data-action="reset"]').addEventListener("click", () => {
            setWidgetValue(node, widgets[DIRECTORY_FIELDS[kind].widget], "");
            renderFolders();
            setStatus(`${DIRECTORY_FIELDS[kind].title} reset to the default downloads folder.`, "info");
        });
    }

    analyzeButton.addEventListener("click", probeUrl);

    render();

    return {
        root,
        state,
        render,
        syncFromWidgets() {
            const migrated = migrateLegacySelection();
            if (!migrated) state.selection = parseSelection(widgets.selection?.value);
            render();
            const rawUrl = String(widgets.url?.value || "").trim();
            const comparedUrl = compareUrl(rawUrl);
            if (comparedUrl && comparedUrl !== state.lastUrl) {
                state.lastUrl = comparedUrl;
                scheduleProbe();
            }
        },
        handleUrlChange,
        dispose() {
            state.disposed = true;
            state.probeId += 1;
            if (state.probeTimer) clearTimeout(state.probeTimer);
            root.replaceChildren();
        },
    };
}


function setupNode(node) {
    if (!isEasyUrlNode(node) || node.__easyUrlPanel) return;

    const widgets = {
        url: findWidget(node, "url"),
        legacyFull: findWidget(node, "download_full_video"),
        legacyAudio: findWidget(node, "download_audio"),
        legacyVideo: findWidget(node, "download_video"),
        selection: findWidget(node, "download_selection"),
        full_output_dir: findWidget(node, "full_output_dir"),
        audio_output_dir: findWidget(node, "audio_output_dir"),
        video_output_dir: findWidget(node, "video_output_dir"),
    };
    if (!widgets.url || !widgets.selection) return;

    hideWidget(widgets.legacyFull);
    hideWidget(widgets.legacyAudio);
    hideWidget(widgets.legacyVideo);
    hideWidget(widgets.selection);
    hideWidget(widgets.full_output_dir);
    hideWidget(widgets.audio_output_dir);
    hideWidget(widgets.video_output_dir);

    const panel = createPanel(node, widgets);
    node.__easyUrlPanel = panel;

    if (!widgets.url.__easyUrlCallback) {
        const originalUrlCallback = widgets.url.callback;
        widgets.url.callback = function (...args) {
            originalUrlCallback?.apply(this, args);
            panel.handleUrlChange(args[0] ?? this.value);
        };
        widgets.url.__easyUrlCallback = true;
    }

    if (!node.__easyUrlConfigureHook) {
        const originalConfigure = node.onConfigure;
        node.onConfigure = function (...args) {
            const result = originalConfigure?.apply(this, args);
            queueMicrotask(() => this.__easyUrlPanel?.syncFromWidgets());
            return result;
        };
        node.__easyUrlConfigureHook = true;
    }

    panel.syncFromWidgets();
    node.setSize?.([
        Math.max(node.size?.[0] || 0, 460),
        Math.max(node.size?.[1] || 0, PANEL_MIN_HEIGHT + 60),
    ]);
    panel.root.parentElement?.classList?.add("easyurl-loader-dom-widget");
}


app.registerExtension({
    name: "ComfyUI.EasyUrlLoader",
    nodeCreated(node) {
        if (isEasyUrlNode(node)) {
            queueMicrotask(() => setupNode(node));
        }
    },
});
