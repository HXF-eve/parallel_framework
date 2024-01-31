package main

import (
	"encoding/json"
	"errors"
	"fmt"
	"github.com/hyperledger/fabric-contract-api-go/contractapi"
)


// SubChainContract contract for handling IoTDatas
type SubChainContract struct {
	contractapi.Contract
}

// NewIoTDevice adds a new IoT device data to the world state using id as key
func (cc *SubChainContract) NewIoTDevice(ctx CustomTransactionContextInterface, id string, deviceId string, time string, payload string) error {
	GetWorldState(ctx)
	existing := ctx.GetData()

	if existing != nil {
		return fmt.Errorf("Cannot create new data in world state as key %s already exists", id)
	}

	iot := new(IoTData)
	iot.DeviceId = deviceId
	iot.Time = time
	iot.Payload = payload

	iotBytes, _ := json.Marshal(iot)

	err := ctx.GetStub().PutState(id, []byte(iotBytes))

	if err != nil {
		return errors.New("Unable to interact with world state")
	}

	return nil
}

// UpdateData changes the time and payload data of a specific device
func (cc *SubChainContract) UpdateIoTData(ctx CustomTransactionContextInterface, id string, newDeviceId string, newTime string, newPayload string) error {
	GetWorldState(ctx)
	existing := ctx.GetData()

	if existing == nil {
		return fmt.Errorf("Cannot update data in world state as key %s does not exist", id)
	}

	iot := new(IoTData)
	iot.DeviceId = newDeviceId
	iot.Time = newTime
	iot.Payload = newPayload

	iotBytes, _ := json.Marshal(iot)

	err := ctx.GetStub().PutState(id, []byte(iotBytes))

	if err != nil {
		return errors.New("Unable to interact with world state")
	}

	return nil
}

// UpdateData changes the time and payload data of a specific device
func (cc *SubChainContract) NewPKData(ctx CustomTransactionContextInterface, id string, payload string) error {
	GetWorldState(ctx)
	existing := ctx.GetData()

	if existing != nil {
		return fmt.Errorf("Cannot create new data in world state as key %s already exists", id)
	}

	pk := new(PKData)
	
	pk.Payload = payload

	pkBytes, _ := json.Marshal(pk)

	err := ctx.GetStub().PutState(id, []byte(pkBytes))

	if err != nil {
		return errors.New("Unable to interact with world state")
	}

	return nil
}

// GetIoTData returns the IoT data with id given from the parameter
func (cc *SubChainContract) GetIoTData(ctx CustomTransactionContextInterface, id string) (*IoTData, error) {
	GetWorldState(ctx)
	existing := ctx.GetData()

	if existing == nil {
		return nil, fmt.Errorf("Cannot read world state pair with key %s. Does not exist", id)
	}

	iot := new(IoTData)

	err := json.Unmarshal(existing, iot)

	if err != nil {
		return nil, fmt.Errorf("Data retrieved from world state for key %s was not of type IoTData", id)
	}

	return iot, nil
}

//GetAllIoTData return all the IoT data on the sub chain
func (cc *SubChainContract) GetAllIoTData(ctx CustomTransactionContextInterface) ([]*IoTData, error) {
	resultsIterator, err := ctx.GetStub().GetStateByRange("", "")
	
	if err != nil {
		return nil, err
	}
	defer resultsIterator.Close()

	var dataList []*IoTData
	for resultsIterator.HasNext() {
		queryResponse, err := resultsIterator.Next()
		if err != nil {
			return nil, err
		}

		var iot IoTData
		err = json.Unmarshal(queryResponse.Value, &iot)
		if err != nil {
			return nil, err
		}
		dataList = append(dataList, &iot)
	}

	return dataList, nil
}

// GetOKData returns the client public key data with id given from the parameter
func (cc *SubChainContract) GetPKData(ctx CustomTransactionContextInterface, id string) (*PKData, error) {
	GetWorldState(ctx)
	existing := ctx.GetData()

	if existing == nil {
		return nil, fmt.Errorf("Cannot read world state pair with key %s. Does not exist", id)
	}

	pk := new(PKData)

	err := json.Unmarshal(existing, pk)

	if err != nil {
		return nil, fmt.Errorf("Data retrieved from world state for key %s was not of type PKData", id)
	}

	return pk, nil
}

//GetAllPKData return all the client public key data on the sub chain
func (cc *SubChainContract) GetAllPKData(ctx CustomTransactionContextInterface) ([]*PKData, error) {
	resultsIterator, err := ctx.GetStub().GetStateByRange("", "")
	
	if err != nil {
		return nil, err
	}
	defer resultsIterator.Close()

	var dataList []*PKData
	for resultsIterator.HasNext() {
		queryResponse, err := resultsIterator.Next()
		if err != nil {
			return nil, err
		}

		var pk PKData
		err = json.Unmarshal(queryResponse.Value, &pk)
		if err != nil {
			return nil, err
		}
		dataList = append(dataList, &pk)
	}

	return dataList, nil
}

func (cc *SubChainContract) DeleteData(ctx CustomTransactionContextInterface, id string) error {
	GetWorldState(ctx)
	existing := ctx.GetData()

	if existing == nil {
		return fmt.Errorf("Cannot read world state pair with key %s. Does not exist", id)
	}

	return ctx.GetStub().DelState(id)
}

// GetEvaluateTransactions returns functions of SubChainContract not to be tagged as submit
func (cc *SubChainContract) GetEvaluateTransactions() []string {
	return []string{"GetIoTData", "GetPKData", "GetAllIoTData", "GetAllPKData"}
}