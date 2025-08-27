(function () {

    const processDataBridge = function (data) {
        let actionsPerformed = 0;

        if (data.replacedPlaceholder) {
            CMS.API.StructureBoard.invalidateState('CLEAR_PLACEHOLDER', data.replacedPlaceholder);
            actionsPerformed++;
        }
        if (data.replacedPlugin) {
            CMS.API.StructureBoard.invalidateState('DELETE', data.replacedPlugin);
            actionsPerformed++;
        }
        if (data.addedPlugins) {
            for (const addedPlugin of data.addedPlugins) {
                CMS.API.StructureBoard.invalidateState('ADD', addedPlugin);
                actionsPerformed++;
            }
        }
        if (data.movedPlugins) {
            for (const movedPlugin of data.movedPlugins) {
                CMS.API.StructureBoard.invalidateState('MOVE', movedPlugin);
                actionsPerformed++;
            }
        }
        return actionsPerformed;
    }

    const iframe = window.parent.document.querySelector('.cms-modal-frame > iframe');
    const {CMS} = window.parent;

    if (!iframe || !CMS) {
        return;
    }

    // Register the event handler in the capture phase to increase the chance it runs first
    iframe.addEventListener('load', function (event) {
        const iframeDocument = iframe.contentDocument || iframe.contentWindow.document;
        const dataBridge = iframeDocument.body.querySelector('script#data-bridge');
        if (dataBridge) {
            try {
                const data = JSON.parse(dataBridge.textContent);
                if (data.action === 'ALIAS_REPLACE') {
                    event.stopPropagation();
                    dataBridge.parentNode.removeChild(dataBridge);
                    if (processDataBridge(data)) {
                    }
                    iframe.dispatchEvent(new Event('load')); // re-dispatch load event to trigger modal close
                }
            } catch (error) {
                window.parent.console.error('Error parsing data bridge script:', error);
            }
            iframeDocument.body.textContent = JSON.stringify(dataBridge);
        }
    }, true); // 'true' sets the event to be handled in the capture phase before the modals handler
})();