const fs = require('node:fs'), vm = require('node:vm'), assert = require('node:assert/strict');
const events = {};
const attrs = {};
const output = {};
const homeLink = { removeAttribute() {}, setAttribute() {} };
const section = { dataset: {homeRoutes: '{"2018":"/myspace/2018/","2020":"/myspace/2020/"}',activityYears:'[2018,2020]'},
 querySelector(selector) {return selector === 'output' ? output : homeLink;}, querySelectorAll() {return [];} };
const control = { value:'2018',min:'2018',max:'2020',dataset:{defaultYear:'2018'},id:'archive-year-global-control',
 closest(selector) {return selector === '.archive-year-global' ? section : null;},
 setAttribute(key,value) {attrs[key]=value;}, addEventListener(name,fn) {events[name]=fn;},
 dispatchEvent() {} };
const document = { documentElement:{classList:{add(){}}},getElementById(){return null;},
 querySelectorAll(selector){return selector === '.archive-year-global-control' ? [control] : [];} };
vm.runInNewContext(fs.readFileSync('public/archive-timeline.js','utf8'), {document,location:{search:''},URLSearchParams,URL,Event,window:{addEventListener(){}}});
assert.ok(events.keydown, 'range needs keyboard navigation over sparse archive years');
events.keydown({key:'ArrowRight',preventDefault(){}});
assert.equal(control.value,'2020');
events.keydown({key:'ArrowLeft',preventDefault(){}});
assert.equal(control.value,'2018');
console.log('Sparse-year keyboard navigation passed');
const resizeHandlers = {};
const historical = {style:{width:'',zoom:''},offsetWidth:800,scrollWidth:800};
const mobileDocument = {documentElement:{clientWidth:390,classList:{add(){}}},body:{clientWidth:390},getElementById(){return null;},querySelectorAll(selector){return selector==='body > .twitter-original'?[historical]:[];}};
const mobileWindow = {innerWidth:390,addEventListener(name,fn){resizeHandlers[name]=fn;}};
vm.runInNewContext(fs.readFileSync('public/archive-timeline.js','utf8'), {document:mobileDocument,location:{pathname:'/twitter-example/captures/2009/',search:''},URLSearchParams,URL,Event,WeakMap,window:mobileWindow});
assert.equal(historical.style.width,'800px');
assert.equal(Number(historical.style.zoom),390/800);
mobileWindow.innerWidth=1200;
resizeHandlers.resize();
assert.equal(historical.style.width,'');
assert.equal(historical.style.zoom,'');
console.log('Mobile fit restores original desktop sizing');
