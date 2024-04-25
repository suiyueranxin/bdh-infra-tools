sap.ui.controller("bdhreport.case_detail_push", {

/**
* Called when a controller is instantiated and its View controls (if available) are already created.
* Can be used to modify the View before it is displayed, to bind event handlers and do other one-time initialization.
* @memberOf bdhreport.case_detail_push
*/
	showJobStatus:function(data) {
		var that = this;
		
		if (data == 'failure' || data == 'error') {
			return "Error";
		}else if(data == 'finished') {
			return "Success";
		}else{
			return "None";
		}
	},
	
	onInit: function() {
		this.getView().addEventDelegate( 
				{
					onBeforeShow : function(evt) {
						var oModel =  this.getView().byId("caseListPush").getModel();			    	
						oModel.setProperty("/currentUser", currentUser);	
									
					}
				}, this);
	},
	
	goBackDBList:function(){
		this.getSplitContObj().toDetail("push_validation_report");
	},
	
	getSplitContObj : function(){
		var result = this.getView().oParent.oParent;
		if(!result){
			jQuery.sap.log.error("SplitApp object can't be found");
		}
		return result;
	},
	
	onCollapseAll: function() {
		var oTreeTable = this.getView().byId('caseListPush');
		oTreeTable.collapseAll();
	},

	onExpandFirstLevel: function() {
		var oTreeTable = this.getView().byId('caseListPush');
		oTreeTable.expandToLevel(1);
	},
	
	messageDialog: null,
	onShowErrorMsg: function(evt) {
		var object = evt.oSource.getBindingContext().getObject();
		if (object.test_state != "ok"){
			var test_stack = evt.oSource.getBindingContext().getObject().test_stack;
			var err_msg = evt.oSource.getBindingContext().getObject().test_message;
					
			var json_data = {dataList: [{item: "Test Stack", value: test_stack}, {item: "Error Message", value: err_msg}]};		
			var oModel = new sap.ui.model.json.JSONModel();
		   	oModel.setData(json_data);
		   	//this.historyDialog.destroy();
			if (!this.messageDialog) {
				this.messageDialog = new sap.m.Dialog({
					title: 'Test Stack and Error Message',
					content: new sap.m.Table({
						  id:"messageList",			  
						  columns:[
						          new sap.m.Column({
						          header:[
						                  new sap.m.Label({
						                  text:"Item"
						                  })
						                  ],
						          width: "6rem"
						          }),new sap.m.Column({
						          header:[
						                  new sap.m.Label({
						                  text:"Value"
						                  })
						                  ]
						          })
						          ],
						  items:{
						        path: '/dataList',
						        template: new sap.m.ColumnListItem({
						        cells:[
						               new sap.m.Text({
						               text:"{item}"
						               }),
						               new sap.m.Text({
						               text:"{value}"
						               })
						               ]
						        })
						  	}	
						  }),
					beginButton: new sap.m.Button({
						text: 'Close',
						press: function () {
							this.messageDialog.close();
						}.bind(this)
					})
				});
				this.getView().addDependent(this.messageDialog);			
				//this.historyDialog.bindElement("/");
				//to get access to the global model			
			}
			this.messageDialog.setModel(oModel);
			this.messageDialog.open();
		} else {
			var msg = 'Test run ok, no further into.';
			sap.m.MessageToast.show(msg);
		}
		
	},
	
	toCaseHistory: function(evt){
		var that = this;
		
		if(evt.oSource.getBindingContext().getObject()){			
			var object = evt.oSource.getBindingContext().getObject();
			var case_id = object.test_id;			
			var catagory_id = evt.oSource.getModel().oData.catagoryId;
			
			var historyList = python_server + "/trd/test/history?catagory_id=" + catagory_id + "&test_id=" + case_id;
			$.ajax({
				url:historyList,
				type:"GET",
				dataType:"json",
	  			success : function(data, textStatus, jqXHR){	  					  				
	  				that.getSplitContObj().toDetail("test_case_history", data);
	  			},
	  			error : function(jqXHR, textStatus, errorThrown) {
	  				jQuery.sap.require("sap.m.MessageBox");
	  				sap.m.MessageBox.error("Can't get test case history!", {
							title: "Error",
							onClose: null,
							styleClass: "",
							initialFocus: null,
							textDirection: sap.ui.core.TextDirection.Inherit
					});
				}
			});
		}
	},

	toJobConsole: function(evt){
		var object = evt.oSource.getBindingContext().getObject();
		if (object && object.hasOwnProperty("job_console_url") && object.job_console_url != "") {
			sap.m.URLHelper.redirect(object.job_console_url, true);
		} else{
			evt.getSource().setActive(false)
		}	
	},
	
	onShowInputDialog: function (evt) {		
		if(evt.oSource.oParent.getBindingContext().getObject()){
			var object = evt.oSource.oParent.getBindingContext().getObject();
			var run_id = object.test_run_id;			
			var test_name = object.test_name;
			inputBugDialog = new sap.m.Dialog({
				title: 'Failure Reason For '+test_name,
				contentWidth: "30rem",
				type: 'Message',
				content: [				
					new sap.m.TextArea('submitDialogTextarea', {
						liveChange: function(oEvent) {
							var sText = oEvent.getParameter('value');
							var parent = oEvent.getSource().getParent();
							var textControl = parent.getContent()[1];
							var reg = /^[0-9]+.?[0-9]*$/;
							if (reg.test(sText)) {			
								textControl.setVisible(false);
								parent.getBeginButton().setEnabled(true);
							} else {								
								textControl.addStyleClass("redText");
								textControl.setText("Only allow bug number, eg:165266,165233");
								textControl.setVisible(true);
								parent.getBeginButton().setEnabled(false);
							}							
						},
						width: '100%',
						placeholder: "Input Bugzilla Number, eg:165266, multiple bugs separator is ','"
					}),
					new sap.m.Text('textForMessage',{
						visible: false,
						text: "Only allow bug number, eg:165266,165233"
					})
				],
				beginButton: new sap.m.Button({
					text: 'Submit',
					enabled: false,
					press: function (evt) {
						var bug = evt.oSource.oParent.getContent()[0].getValue();
						var textController = evt.oSource.oParent.getContent()[1];
						
						var updateBugUrl = python_server + "/trd/test/update?run_id=" + run_id + "&bug=" + bug;
						$.ajax({
							url:updateBugUrl,
							type:"PATCH",
							dataType:"json",
				  			success : function(data, textStatus, jqXHR){
				  				if(data.status == "200"){
				  					inputBugDialog.close();
				  					sap.m.MessageToast.show(data.message);													  					
				  				} else {
				  					textController.setText(data.message);
				  					textController.setVisible(true);
				  				}
				  			},
				  			error : function(jqXHR, textStatus, errorThrown) {
				  				textController.setText("Error: Fail to update bug info for test case!");
				  				textController.setVisible(true);				  				
							}
						});
					}
				}),
				endButton: new sap.m.Button({
					text: 'Cancel',
					press: function () {
						inputBugDialog.close();
					}
				}),
				afterClose: function() {
					inputBugDialog.destroy();
				}
			});
	        inputBugDialog.open();
		}						
	},
/**
* Similar to onAfterRendering, but this hook is invoked before the controller's View is re-rendered
* (NOT before the first rendering! onInit() is used for that one!).
* @memberOf eim2_0ui.db_detail
*/
//	onBeforeRendering: function() {
//
//	},

/**
* Called when the View has been rendered (so its HTML is part of the document). Post-rendering manipulations of the HTML could be done here.
* This hook is the same one that SAPUI5 controls get after being rendered.
* @memberOf eim2_0ui.db_detail
*/
//	onAfterRendering: function() {
//
//	},

/**
* Called when the Controller is destroyed. Use this one to free resources and finalize activities.
* @memberOf eim2_0ui.db_detail
*/
//	onExit: function() {
//
//	}

});