/**
 * Polyfills for older browsers
 * These polyfills help ensure our UI works in all environments including ReadTheDocs
 */
(function() {
    // Array.from polyfill for IE11
    if (!Array.from) {
        Array.from = function(iterable) {
            if (iterable == null) {
                throw new TypeError('Array.from requires an array-like object');
            }
            
            var arr = [];
            var len = iterable.length;
            for (var i = 0; i < len; i++) {
                arr.push(iterable[i]);
            }
            return arr;
        };
    }
    
    // Element.matches polyfill for older browsers
    if (!Element.prototype.matches) {
        Element.prototype.matches = 
            Element.prototype.matchesSelector || 
            Element.prototype.mozMatchesSelector ||
            Element.prototype.msMatchesSelector || 
            Element.prototype.oMatchesSelector || 
            Element.prototype.webkitMatchesSelector ||
            function(s) {
                var matches = (this.document || this.ownerDocument).querySelectorAll(s),
                    i = matches.length;
                while (--i >= 0 && matches.item(i) !== this) {}
                return i > -1;            
            };
    }
    
    // NodeList.forEach polyfill for IE
    if (window.NodeList && !NodeList.prototype.forEach) {
        NodeList.prototype.forEach = Array.prototype.forEach;
    }
    
    // Element.closest polyfill
    if (!Element.prototype.closest) {
        Element.prototype.closest = function(s) {
            var el = this;
            do {
                if (el.matches(s)) return el;
                el = el.parentElement || el.parentNode;
            } while (el !== null && el.nodeType === 1);
            return null;
        };
    }
    
    // CustomEvent polyfill for IE
    if (typeof window.CustomEvent !== 'function') {
        function CustomEvent(event, params) {
            params = params || { bubbles: false, cancelable: false, detail: null };
            var evt = document.createEvent('CustomEvent');
            evt.initCustomEvent(event, params.bubbles, params.cancelable, params.detail);
            return evt;
        }
        
        window.CustomEvent = CustomEvent;
    }
})(); 