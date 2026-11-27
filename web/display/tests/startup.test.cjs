const assert = require("node:assert/strict");
const { readFileSync } = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const { test } = require("node:test");

function createDisplay(search = "") {
	const elements = new Map();
	const handlers = {};
	const requests = [];
	const timers = [];
	const subscriptions = [];
	function element(id) {
		if (!elements.has(id)) {
			const classes = new Set(["log", "displayTarget"].includes(id) ? ["hide"] : []);
			elements.set(id, {
				textContent: "",
				src: id === "displayTarget" ? "about:blank" : "",
				style: {},
				classList: {
					add: (name) => classes.add(name),
					remove: (name) => classes.delete(name),
					contains: (name) => classes.has(name),
				},
				scrollTo() {},
			});
		}
		return elements.get(id);
	}
	const context = vm.createContext({
		console: { debug() {}, warn() {} },
		URLSearchParams,
		location: {
			protocol: "http:",
			host: "secondary:8080",
			hostname: "secondary",
			port: "8080",
			search,
			href: "",
		},
		document: {
			getElementById: element,
			querySelector: (selector) => element(selector.slice(1)),
		},
		mqtt: {
			connect: () => ({
				on: (event, handler) => { handlers[event] = handler; },
				subscribe: (topic) => subscriptions.push(topic),
			}),
		},
		XMLHttpRequest: class {
			constructor() { requests.push(this); }
			open(method, url) { this.url = url; }
			send() {}
		},
		setTimeout: (callback) => timers.push(callback),
	});
	for (const filename of ["processAllMqttMsg.js", "setupMqttServices.js"]) {
		vm.runInContext(readFileSync(path.join(__dirname, "..", filename), "utf8"), context);
	}
	handlers.connect({});
	return {
		context, element, requests, timers, subscriptions,
		receive(topic, payload) { handlers.message(topic, JSON.stringify(payload)); },
	};
}

function sendCommon(display, secondary = true, bootDone = true, updating = false) {
	for (const [topic, value] of Object.entries({
		"openWB/system/version": "2.3.0-alpha.1",
		"openWB/system/boot_done": bootDone,
		"openWB/system/update_in_progress": updating,
		"openWB/system/security/user_management_active": false,
		"openWB/general/extern": secondary,
	})) {
		display.receive(topic, value);
	}
}

function sendLocalTheme(display) {
	display.receive("openWB/optional/int_display/theme", {
		type: "url_display",
		configuration: { url: "http://192.168.199.254" },
	});
	display.receive("openWB/optional/int_display/only_local_charge_points", false);
}

function localDisplay() {
	const display = createDisplay();
	sendCommon(display);
	sendLocalTheme(display);
	display.receive("openWB/general/extern_display_mode", "local");
	return display;
}

test("secondary local mode starts without any parent data or secondary metadata", () => {
	const display = localDisplay();
	assert.equal(display.context.allTopicsReceived(), true);
	assert.equal(display.context.totalTopicCount(), 8);
	assert.equal(display.element("progress-value").style.width, "100%");
	assert.equal(display.requests.length, 1);
	assert.equal(display.requests[0].url,
		"http://secondary:8080/openWB/web/display/themes/url_display/?");
	Object.assign(display.requests[0], { readyState: 4, status: 200 });
	display.requests[0].onload();
	display.timers.forEach((callback) => callback());
	assert.equal(display.element("displayTarget").src, display.requests[0].url);
	assert.equal(display.element("displayTarget").classList.contains("hide"), false);
	assert.equal(display.element("notReady").classList.contains("hide"), true);
	assert.equal(display.context.location.href, "");
});

test("secondary waits for its display mode before choosing a destination", () => {
	const display = createDisplay();
	sendCommon(display);
	sendLocalTheme(display);
	assert.equal(display.context.allTopicsReceived(), false);
	assert.equal(display.requests.length, 0);
	assert.equal(display.timers.length, 0);
	assert.ok(display.context.missingTopicNames().includes("openWB/general/extern_display_mode"));
});

test("local mode waits for local theme settings without extra on-screen logging", () => {
	const display = createDisplay();
	sendCommon(display);
	display.receive("openWB/general/extern_display_mode", "local");
	display.receive("openWB/optional/int_display/only_local_charge_points", false);
	assert.equal(display.requests.length, 0);
	assert.equal(display.context.missingTopics(), 1);
	assert.deepEqual(Array.from(display.context.missingTopicNames()),
		["openWB/optional/int_display/theme"]);
	assert.ok(!display.element("log").textContent.includes("Waiting for MQTT topics:"));
	sendLocalTheme(display);
	assert.equal(display.context.allTopicsReceived(), true);
});

test("primary loads its local theme without secondary topics", () => {
	const display = createDisplay();
	sendCommon(display, false);
	sendLocalTheme(display);
	assert.equal(display.context.allTopicsReceived(), true);
	assert.equal(display.context.totalTopicCount(), 7);
	assert.equal(display.requests.length, 1);
});

test("secondary primary mode still waits for parent data and forwards null mappings", () => {
	const display = createDisplay();
	sendCommon(display);
	for (const [topic, value] of Object.entries({
		"openWB/system/ip_address": "172.16.0.4",
		"openWB/system/current_branch": "test",
		"openWB/system/current_commit": "123456",
		"openWB/general/extern_display_mode": "primary",
		"openWB/internal_chargepoint/0/data/parent_cp": null,
		"openWB/internal_chargepoint/1/data/parent_cp": null,
	})) {
		display.receive(topic, value);
	}
	assert.equal(display.context.missingTopics(), 1);
	assert.deepEqual(Array.from(display.context.missingTopicNames()),
		["openWB/internal_chargepoint/global_data"]);
	assert.equal(display.timers.length, 0);
	display.receive("openWB/internal_chargepoint/global_data", { parent_ip: "primary" });
	assert.equal(display.context.allTopicsReceived(), true);
	assert.equal(display.requests.length, 0);
	display.timers.forEach((callback) => callback());
	const destination = new URL(display.context.location.href);
	assert.equal(destination.host, "primary");
	const forwarded = JSON.parse(destination.searchParams.get("data"));
	assert.equal(forwarded.localIp, "172.16.0.4");
	assert.equal(forwarded.parentChargePoint1, null);
	assert.equal(forwarded.parentChargePoint2, null);
});

test("switching from primary to local mode drops missing parent requirements", () => {
	const display = createDisplay();
	sendCommon(display);
	sendLocalTheme(display);
	display.receive("openWB/general/extern_display_mode", "primary");
	assert.equal(display.requests.length, 0);
	display.receive("openWB/general/extern_display_mode", "local");
	assert.equal(display.context.allTopicsReceived(), true);
	assert.equal(display.requests.length, 1);
});

for (const [bootDone, updating, message] of [
	[false, false, "backend still booting"],
	[true, true, "update in progress"],
]) {
	test(`local mode respects startup guard: ${message}`, () => {
		const display = createDisplay();
		sendCommon(display, true, bootDone, updating);
		sendLocalTheme(display);
		display.receive("openWB/general/extern_display_mode", "local");
		assert.equal(display.requests.length, 0);
		assert.ok(display.element("log").textContent.endsWith(message));
		assert.equal(display.element("displayTarget").classList.contains("hide"), true);
	});
}

for (const [event, expected] of [
	["onload", "HTTP 404"],
	["onerror", "network error"],
	["ontimeout", "timed out"],
]) {
	test(`theme request ${event} failure is visible on the display`, () => {
		const display = localDisplay();
		Object.assign(display.requests[0], { readyState: 4, status: 404 });
		display.requests[0][event]();
		assert.ok(display.element("log").textContent.includes(expected));
		assert.equal(display.element("log").classList.contains("hide"), false);
		assert.equal(display.element("displayTarget").src, "about:blank");
	});
}

test("local theme preserves forwarded data and login suppression", () => {
	const display = createDisplay("?data=%7B%22localIp%22%3A%22secondary%22%7D");
	sendCommon(display);
	display.context.credentialsFetched = true;
	sendLocalTheme(display);
	display.receive("openWB/general/extern_display_mode", "local");
	const destination = new URL(display.requests[0].url);
	assert.equal(destination.searchParams.get("data"), '{"localIp":"secondary"}');
	assert.equal(destination.searchParams.get("hide_login"), "1");
});

for (const [secondary, mode, expectedGroup] of [
	[undefined, undefined, "primary"],
	[false, undefined, "primary"],
	[false, "primary", "primary"],
	[false, "local", "primary"],
	[true, undefined, "secondary"],
	[true, null, "secondary"],
	[true, "primary", "secondary"],
	[true, "unknown", "secondary"],
	[true, "local", "local"],
]) {
	test(`readiness requirements: secondary=${secondary}, mode=${mode}`, () => {
		const { context, subscriptions } = createDisplay();
		context.data["openWB/general/extern"] = secondary;
		context.data["openWB/general/extern_display_mode"] = mode;
		const common = context.topicsToSubscribe;
		const primary = context.primaryTopicsToSubscribe;
		const remote = context.secondaryTopicsToSubscribe;
		const expected = [
			...Object.keys(common),
			...Object.keys(expectedGroup === "secondary" ? remote : primary),
			...(expectedGroup === "local" ? ["openWB/general/extern_display_mode"] : []),
		];
		assert.deepEqual(Object.keys(context.requiredTopics()).sort(), expected.sort());
		assert.equal(context.totalTopicCount(), expected.length);
		assert.equal(context.missingTopics(), expected.length);
		assert.deepEqual(subscriptions.sort(),
			[...Object.keys(common), ...Object.keys(primary), ...Object.keys(remote)].sort());

		for (const group of [common, primary, remote]) {
			for (const topic of Object.keys(group)) {
				group[topic] = true;
			}
		}
		assert.equal(context.allTopicsReceived(), true);
		for (const group of [common, primary, remote]) {
			for (const topic of Object.keys(group)) {
				group[topic] = false;
				const required = expected.includes(topic);
				assert.equal(context.missingTopics(), required ? 1 : 0, topic);
				assert.equal(context.allTopicsReceived(), !required, topic);
				group[topic] = true;
			}
		}
	});
}

test("receiving local mode before the device role does not start the theme early", () => {
	const display = createDisplay();
	display.receive("openWB/general/extern_display_mode", "local");
	sendLocalTheme(display);
	assert.equal(display.requests.length, 0);
	sendCommon(display);
	assert.equal(display.context.allTopicsReceived(), true);
	assert.equal(display.requests.length, 1);
});
