sap.ui.controller("bdhreport.login", {
    btnClicked: function(){
        this.userName = this.byId('userID').getValue();
        //loading the second view but not placed anywhere, just for showing code usage
        sap.ui.view({id:"myTickePage", viewName:"app.ticket", type:sap.ui.core.mvc.ViewType.JS});
    }
});