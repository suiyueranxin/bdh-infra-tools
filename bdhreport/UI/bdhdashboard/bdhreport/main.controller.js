var python_server = "https://mo-be4e098da.mo.sap.corp:50005/api/v1";
//var python_server = "http://mo-be4e098da.mo.sap.corp:50015/api/v1";
var catagory = "";
var project = "";
var currentMasterVersion = "";

sap.ui.controller("bdhreport.main", {

/**
* Called when a controller is instantiated and its View controls (if available) are already created.
* Can be used to modify the View before it is displayed, to bind event handlers and do other one-time initialization.
* @memberOf bdhreport.main
*/
	
	/**
	* Called when the View has been rendered (so its HTML is part of the document). Post-rendering manipulations of the HTML could be done here.
	* This hook is the same one that SAPUI5 controls get after being rendered.
	* @memberOf buglist.main
	*/
	

	onInit: function() {
		var that = this;
		that.getView().byId("web_userName").setText(currentUser);
		var oSplitCont = that.getSplitContObj();
		
		oSplitCont.addDetailPage(sap.ui.view({
			id:"nightly_validation_report",
			viewName:"bdhreport.nightly_validation_report",
			type:sap.ui.core.mvc.ViewType.XML
		}));
			
		oSplitCont.addDetailPage(sap.ui.view({
			id:"push_validation_report",
			viewName:"bdhreport.push_validation_report",
			type:sap.ui.core.mvc.ViewType.XML
		}));
		
		oSplitCont.addDetailPage(sap.ui.view({
			id:"case_detail_push",
			viewName:"bdhreport.case_detail_push",
			type:sap.ui.core.mvc.ViewType.XML
		}));
		
		oSplitCont.addDetailPage(sap.ui.view({
			id:"case_detail_nightly",
			viewName:"bdhreport.case_detail_nightly",
			type:sap.ui.core.mvc.ViewType.XML
		}));
		
		oSplitCont.addDetailPage(sap.ui.view({
			id:"test_case_history",
			viewName:"bdhreport.test_case_history",
			type:sap.ui.core.mvc.ViewType.XML
		}));			
	},
	
	onListItemPress: function(oEvent){
		var sToPageId = oEvent.getParameter("listItem").getCustomData()[0].getValue();
		this.getSplitContObj().toDetail(sToPageId);
	},
	
	
	getSplitContObj : function(){
		var result = this.byId("SplitCont");
		if(!result){
			jQuery.sap.log.error("SplitApp object can't be found");
		}
		return result;
	},
		
	onCatagorySelect: function(){
		var that = this;
		var catagory_id = that.getView().byId('catagoryBox').getSelectedKey();
		that.getView().byId('versionBox').setValue("");
		that.getView().byId('branchBox').setValue("");
			   	
	    var projectUrl = python_server+"/trd/project?catagory_id=" + catagory_id;
		$.ajax({
			url:projectUrl,
			type:"GET",
			dataType:"json",			
		    success : function(data, textStatus, jqXHR){		    		        
		    	var oModel = new sap.ui.model.json.JSONModel(data);		        
		        that.getView().byId('projectBox').setModel(oModel);		
		    },
		    error : function(jqXHR, textStatus, errorThrown) {			    	
			    sap.m.MessageToast.show("Error");
			}
		});
	},
	
	nightlyItemPress: function(oControlEvent) {
		var that = this;		
		project = oControlEvent.getSource().getTitle();
		catagory = "BDH Nightly Validation";		
		
		var version = '';
		var branch = '';
		
        
        postData = {environment:{}};
        postData.environment.GERRIT_PROJECT = project;
        if(version!=''){postData.environment.VORA_VERSION = version;}
        if (catagory == "BDH Nightly Validation") {
        	postData.environment.USE_FOR = "NIGHTLY_VALIDATION";
        	var tableController = that.getSplitContObj().getPage("nightly_validation_report").byId("reportTableForNightly");       	
        } 
        if (catagory == "BDH Push Validation") {
        	postData.environment.USE_FOR = "PUSH_VALIDATION";
        	if(branch!=''){postData.environment.GERRIT_CHANGE_BRANCH = branch;}
        	var tableController = that.getSplitContObj().getPage("push_validation_report").byId('reportTableForPushV');               	
        }
        
		tableController.setBusy(true);
		
		var emptyData = {"results":[]};
        var oEmptyModel = new sap.ui.model.json.JSONModel();
        oEmptyModel.setData(emptyData);
        tableController.setModel(oEmptyModel);
        
        var reportUrl = python_server+"/trd/search";

		$.ajax({
			url:reportUrl,
			type:"POST",
			dataType:"json",			
			data: JSON.stringify(postData),
		    success : function(data, textStatus, jqXHR){
		    	for(var i=0; i<data.dataList.length; i++){
		    		start = new Date(data.dataList[i].start_time);
		    		end = new Date(data.dataList[i].end_time);
		    		if (start != null && end != null && start != 'Invalid Date' && end != 'Invalid Date'){		    			
			    		data.dataList[i].duration = (parseInt(end - start)/1000/60/60).toFixed(2);
		    		} else{
		    			data.dataList[i].duration = "NULL"
		    		}				    		
		    	}
		    	
		    	var oModel = new sap.ui.model.json.JSONModel();		    	
			   	oModel.setData(data);		    	
			   	tableController.setModel(oModel);
			   	
			   	tableController.setBusy(false);
		    },
		    error : function(jqXHR, textStatus, errorThrown) {
		    	tableController.setBusy(false);
			    sap.m.MessageToast.show("Error");
			}
		});
        	
	},
	
	pushItemPress: function(oControlEvent) {
		var that = this;		
		project = oControlEvent.getSource().getTitle();
		catagory = "BDH Push Validation";		
		        
        postData = {environment:{}};
        postData.environment.GERRIT_PROJECT = project; 
       
        if (catagory == "BDH Nightly Validation") {
        	postData.environment.USE_FOR = "NIGHTLY_VALIDATION";
        	var currentPageView = that.getSplitContObj().getPage("nightly_validation_report");
        	var tableController = currentPageView.byId("reportTableForNightly");        	
        } 
        if (catagory == "BDH Push Validation") {
        	postData.environment.USE_FOR = "PUSH_VALIDATION";     
        	var currentPageView = that.getSplitContObj().getPage("push_validation_report");
        	var tableController = currentPageView.byId('reportTableForPushV');       	       	
        }
        
		tableController.setBusy(true);
		
		var emptyData = {"results":[]};
        var oEmptyModel = new sap.ui.model.json.JSONModel();
        oEmptyModel.setData(emptyData);
        tableController.setModel(oEmptyModel);
        
        var reportUrl = python_server+"/trd/search";

		$.ajax({
			url:reportUrl,
			type:"POST",
			dataType:"json",			
			data: JSON.stringify(postData),
		    success : function(data, textStatus, jqXHR){
		    	for(var i=0; i<data.dataList.length; i++){
		    		start = new Date(data.dataList[i].start_time);
		    		end = new Date(data.dataList[i].end_time);
		    		if (start != null && end != null && start != 'Invalid Date' && end != 'Invalid Date'){		    			
			    		data.dataList[i].duration = (parseInt(end - start)/1000/60/60).toFixed(2);
		    		} else{
		    			data.dataList[i].duration = "NULL"
		    		}				    		
		    	}
		    	var oModel = new sap.ui.model.json.JSONModel();		    	
			   	oModel.setData(data);		    	
			   	tableController.setModel(oModel);
			   	
			   	//prepare version/branch data
//			   	var versionData = {list: [], data:[]};
//		    	var branchData = {list: [], data: []};
//		    	
//		    	for(var i=0; i<data.dataList.length; i++){
//		    		if (data.dataList[i].hasOwnProperty("branch") && branchData.data.indexOf(data.dataList[i].branch) < 0){
//		    			branchData.list.push({"branch": data.dataList[i].branch});
//		    			branchData.data.push(data.dataList[i].branch);
//		    		}
//		    		if (data.dataList[i].hasOwnProperty("vora_version")){
//		    			if (data.dataList[i].vora_version == "null" || data.dataList[i].vora_version == "NULL"){
//		    				var version = "null";	
//		    				var nullVersionData = {version: version};
//		    			} else {
//		    				var index = data.dataList[i].vora_version.lastIndexOf("\.");
//			    			var version = data.dataList[i].vora_version.substring(0,index);			    			
//		    			}
//		    			if (versionData.data.indexOf(version) < 0 && version != "null") {
//		    				if (versionData.data.length == 0) {
//		    					versionData.list.push({"version": version});
//			    				versionData.data.push(version);
//		    				} else{
//		    					if (version > versionData.data[0]){
//		    						versionData.list.unshift({"version": version});
//				    				versionData.data.unshift(version);
//		    					} else{
//		    						versionData.list.push({"version": version});
//				    				versionData.data.push(version);
//		    					}
//		    				}		    				
//		    			}	   
//		    		}		    		
//		    	}
//		    	if (nullVersionData){
//		    		versionData.list.push(nullVersionData);
//		    	}
//		    	currentMasterVersion = versionData.data[0];
//		    	versionData.list.unshift({version: "ALL"});
//		    	branchData.list.unshift({branch: "ALL"})	    	
//		    	
//		    	var versionModel = new sap.ui.model.json.JSONModel();		    	
//		    	versionModel.setData(versionData);		    	
//		    	currentPageView.byId('versionList').setModel(versionModel);
//			   	
//			   	var branchModel = new sap.ui.model.json.JSONModel();		    	
//			   	branchModel.setData(branchData);		    	
//			   	currentPageView.byId('branchList').setModel(branchModel);
//			   	
//			   	if (currentPageView.byId('branchList').getFirstItem().getKey() == "master"){
//			   		currentPageView.byId('versionList').setSelectedKey(currentMasterVersion);
//			   		currentPageView.byId('versionList').setEnabled(false);
//			   	}
			   	
			   	tableController.setBusy(false);
		    },
		    error : function(jqXHR, textStatus, errorThrown) {
		    	tableController.setBusy(false);
			    sap.m.MessageToast.show("Error");
			}
		});
        	
	},
	
	goToNightlyNav:function(){
		this.getSplitContObj().toMaster(this.createId("master2"));
	},
	
	goToPushNav:function(){
		this.getSplitContObj().toMaster(this.createId("master3"));
	},
	
	/**
	 * hide or show navigation
	 */
	onPressHideLeftBar : function(){
		if (this.getSplitContObj().getMode() == "HideMode") {
			this.getSplitContObj().setMode(sap.m.SplitAppMode.ShowHideMode);
		} else {
			this.getSplitContObj().setMode(sap.m.SplitAppMode.HideMode);
		}
	},
	
	onPressBackMain: function(){
		this.getSplitContObj().backMaster(this.createId("master"));
	},
	
	loginDialog: null,
	onLogin: function(){
		var that = this;
		if (!that.loginDialog) {
			that.loginDialog = new sap.m.Dialog({
				title: 'User Login',
				content: [
				      new sap.ui.layout.form.SimpleForm({
				    	  layout: "ResponsiveGridLayout",
				    	  editable:true,
				    	  maxContainerCols:2,
				  			labelSpanL:4,
				  			labelSpanM:2,				  			
				  			emptySpanL:0,
				  			emptySpanM:0,				  			
				  			columnsL:2,
				  			columnsM:2,
				    	  content: [
								new sap.m.Label({text:"User ID", width:"6rem"}),
								new sap.m.Input(that.createId("uid"), {placeholder:"User ID", width:"4rem"}),
								new sap.m.Label({text:"Password", width:"6rem"}),
								new sap.m.Input(that.createId("passw"), {placeholder:"Password", type:"Password", width:"4rem"})
				    	          ]
				      })
//				      new sap.m.HBox({
//				    	  items: [
//				    	          new sap.m.VBox({
//				    	        	  items:[
//				    	        	         new sap.m.Label({text:"User ID", width:"6rem"}),
//				    	        	         new sap.m.Input(that.createId("uid"), {placeholder:"User ID"})
//				    	        	         ]
//				    	          })
//				    	          
//				    	  ]
//				      }),
//				      new sap.m.HBox({
//				    	  items: [
//								new sap.m.VBox({
//									  items:[
//									         new sap.m.Label({text:"Password", width:"6rem"}),
//									         new sap.m.Input(that.createId("passw"), {placeholder:"Password", type:"Password"}),
//									         ]
//								})				    	          
//				    	  ]
//				      })			              				          
				],
				beginButton: new sap.m.Button({
					text: 'Login',
					press: function () {
						currentUser = that.getView().byId("uid").getValue();
              		    that.getView().byId("web_userName").setText(currentUser);	                		  	          			   	            			             			   	  
              		    that.loginDialog.close();
					}
				}),
				endButton: new sap.m.Button({
					text: 'Cancel',
					press: function () {
						that.loginDialog.close();
					}
				})
			});
		}		
		that.loginDialog.open();
	},
});