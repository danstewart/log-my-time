import{Controller}from'../controller.js';import{parseDuration,parseBoolean}from'../util.js';function asyncGeneratorStep(gen,resolve,reject,_next,_throw,key,arg){try{var info=gen[key](arg);var value=info.value}catch(error){reject(error);return}if(info.done){resolve(value)}else{Promise.resolve(value).then(_next,_throw)}}function _asyncToGenerator(fn){return function(){var self=this,args=arguments;return new Promise(function(resolve,reject){var gen=fn.apply(self,args);function _next(value){asyncGeneratorStep(gen,resolve,reject,_next,_throw,"next",value)}function _throw(err){asyncGeneratorStep(gen,resolve,reject,_next,_throw,"throw",err)}_next(undefined)})}}class DynamicFrame extends Controller{init(){var _this=this;return _asyncToGenerator(function*(){_this.contents='';_this._reqAbort=[];_this.autoRefresh=parseBoolean(_this.autoRefresh);_this.executeScripts=parseBoolean(_this.executeScripts);if(_this.autoRefresh){const interval=parseDuration(_this.autoRefresh);_this.setAutoRefresh(interval)}if(!_this.delay)_this.delay=0})()}refresh(){var _this=this;return _asyncToGenerator(function*(){yield _this.render()})()}render(){var _this=this,_superprop_get_render=()=>super.render;return _asyncToGenerator(function*(){yield _this.loadContent();yield _superprop_get_render().call(_this)})()}bind(){super.bind();if(this.mountPoint&& typeof this.mountPoint==='string'){this.mountPoint=this.querySelector(this.mountPoint)}if(!this.mountPoint){this.mountPoint=this.root}}setAutoRefresh(interval){if(interval===undefined){console.error(`[${this.tag}] Undefined interval passed to setAutoRefresh`);return}if(this.__internal__.autoRefreshInterval){window.clearInterval(this.__internal__.autoRefreshInterval)}this.__internal__.autoRefreshInterval=window.setInterval(()=>this.refresh(),interval)}loadContent(e,mode='replace'){var _this=this;return _asyncToGenerator(function*(){let url=_this.endpoint();url.search=new URLSearchParams(_this.params());_this._reqAbort.forEach(controller=>controller.abort());_this._reqAbort=[];const abortController=new AbortController();_this._reqAbort.push(abortController);let ok=true;const sendReq=function(){var _ref=_asyncToGenerator(function*(){try{let response=yield fetch(url,{signal:abortController.signal});let text=yield response.text();_this.updateContent(text);_this.findAndExecuteScripts()}catch(err){console.error(err);ok=false}});return function sendReq(){return _ref.apply(this,arguments)}}();yield Promise.allSettled([new Promise(resolve=>setTimeout(resolve,_this.delay)),sendReq(),]);return ok})()}findAndExecuteScripts(){if(this.executeScripts!=="true")return;let scripts=this.querySelectorAll('script');if(!scripts)return;[...scripts].forEach(script=>{let newScript=document.createElement("script");newScript.setAttribute("type","text/javascript");if(script.getAttribute("src")){newScript.setAttribute("src",script.getAttribute("src"));this.appendChild(newScript)}else{newScript.appendChild(document.createTextNode(script.innerHTML));this.appendChild(newScript)}})}updateContent(content,mode='replace'){if(mode==='replace'){this.mountPoint.innerHTML=content}else if(mode==='append'){this.mountPoint.insertAdjacentHTML('beforeEnd',content)}}params(values={}){let params=new URLSearchParams(values);Object.entries(values).forEach(([key,val])=>{if(Array.isArray(val)){params.delete(key);val.forEach(item=>params.append(key,item))}});for(let attr of this.root.attributes){if(attr.nodeName.startsWith(":param-")){params.append(attr.nodeName.substr(7),attr.nodeValue)}}return params}endpoint(){let url=this.url;if(!this.url){console.error(`${this.tag}: No :url attribute specified`);return}if(!url.startsWith('http'))url=window.location.origin+url;return new URL(url)}}export{DynamicFrame}