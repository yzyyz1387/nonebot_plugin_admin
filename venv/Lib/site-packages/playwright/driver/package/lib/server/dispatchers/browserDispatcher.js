"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.ConnectedBrowserDispatcher = exports.BrowserDispatcher = void 0;

var _browser = require("../browser");

var _browserContextDispatcher = require("./browserContextDispatcher");

var _cdpSessionDispatcher = require("./cdpSessionDispatcher");

var _dispatcher = require("./dispatcher");

var _instrumentation = require("../instrumentation");

var _browserContext = require("../browserContext");

var _selectors = require("../selectors");

/**
 * Copyright (c) Microsoft Corporation.
 *
 * Licensed under the Apache License, Version 2.0 (the 'License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
class BrowserDispatcher extends _dispatcher.Dispatcher {
  constructor(scope, browser) {
    super(scope, browser, 'Browser', {
      version: browser.version(),
      name: browser.options.name
    }, true);
    this._type_Browser = true;
    this._contextForReuse = void 0;
    this.addObjectListener(_browser.Browser.Events.Disconnected, () => this._didClose());
  }

  _didClose() {
    this._dispatchEvent('close');

    this._dispose();
  }

  async newContext(params, metadata) {
    const context = await this._object.newContext(metadata, params);
    return {
      context: new _browserContextDispatcher.BrowserContextDispatcher(this._scope, context)
    };
  }
  /**
   * Used for inner loop scenarios where user would like to preserve the browser window, opened page and devtools instance.
   */


  async newContextForReuse(params, metadata) {
    const hash = _browserContext.BrowserContext.reusableContextHash(params);

    if (!this._contextForReuse || hash !== this._contextForReuse.hash || !this._contextForReuse.context.canResetForReuse()) {
      if (this._contextForReuse) await this._contextForReuse.context.close(metadata);
      this._contextForReuse = {
        context: await this._object.newContext(metadata, params),
        hash
      };
    } else {
      const oldContextDispatcher = (0, _dispatcher.existingDispatcher)(this._contextForReuse.context);

      oldContextDispatcher._dispose();

      await this._contextForReuse.context.resetForReuse(metadata, params);
    }

    const context = new _browserContextDispatcher.BrowserContextDispatcher(this._scope, this._contextForReuse.context);
    return {
      context
    };
  }

  async close() {
    await this._object.close();
  }

  async killForTests() {
    await this._object.killForTests();
  }

  async newBrowserCDPSession() {
    if (!this._object.options.isChromium) throw new Error(`CDP session is only available in Chromium`);
    const crBrowser = this._object;
    return {
      session: new _cdpSessionDispatcher.CDPSessionDispatcher(this._scope, await crBrowser.newBrowserCDPSession())
    };
  }

  async startTracing(params) {
    if (!this._object.options.isChromium) throw new Error(`Tracing is only available in Chromium`);
    const crBrowser = this._object;
    await crBrowser.startTracing(params.page ? params.page._object : undefined, params);
  }

  async stopTracing() {
    if (!this._object.options.isChromium) throw new Error(`Tracing is only available in Chromium`);
    const crBrowser = this._object;
    return {
      binary: await crBrowser.stopTracing()
    };
  }

} // This class implements multiplexing browser dispatchers over a single Browser instance.


exports.BrowserDispatcher = BrowserDispatcher;

class ConnectedBrowserDispatcher extends _dispatcher.Dispatcher {
  constructor(scope, browser) {
    super(scope, browser, 'Browser', {
      version: browser.version(),
      name: browser.options.name
    }, true); // When we have a remotely-connected browser, each client gets a fresh Selector instance,
    // so that two clients do not interfere between each other.

    this._type_Browser = true;
    this._contexts = new Set();
    this.selectors = void 0;
    this.selectors = new _selectors.Selectors();
  }

  async newContext(params, metadata) {
    if (params.recordVideo) params.recordVideo.dir = this._object.options.artifactsDir;
    const context = await this._object.newContext(metadata, params);

    this._contexts.add(context);

    context.setSelectors(this.selectors);
    context.on(_browserContext.BrowserContext.Events.Close, () => this._contexts.delete(context));
    return {
      context: new _browserContextDispatcher.BrowserContextDispatcher(this._scope, context)
    };
  }

  newContextForReuse(params, metadata) {
    throw new Error('Method not implemented.');
  }

  async close() {// Client should not send us Browser.close.
  }

  async killForTests() {// Client should not send us Browser.killForTests.
  }

  async newBrowserCDPSession() {
    if (!this._object.options.isChromium) throw new Error(`CDP session is only available in Chromium`);
    const crBrowser = this._object;
    return {
      session: new _cdpSessionDispatcher.CDPSessionDispatcher(this._scope, await crBrowser.newBrowserCDPSession())
    };
  }

  async startTracing(params) {
    if (!this._object.options.isChromium) throw new Error(`Tracing is only available in Chromium`);
    const crBrowser = this._object;
    await crBrowser.startTracing(params.page ? params.page._object : undefined, params);
  }

  async stopTracing() {
    if (!this._object.options.isChromium) throw new Error(`Tracing is only available in Chromium`);
    const crBrowser = this._object;
    return {
      binary: await crBrowser.stopTracing()
    };
  }

  async cleanupContexts() {
    await Promise.all(Array.from(this._contexts).map(context => context.close((0, _instrumentation.serverSideCallMetadata)())));
  }

}

exports.ConnectedBrowserDispatcher = ConnectedBrowserDispatcher;