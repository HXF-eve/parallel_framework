package main

import (
	"encoding/json"
	"errors"
	"fmt"
	"github.com/hyperledger/fabric-contract-api-go/contractapi"
)


// MainChainContract contract for handling IoTDatas
type MainChainContract struct {
	contractapi.Contract
}

func (cc *MainChainContract) NewPKData(ctx CustomTransactionContextInterface, id string,  payload string) error {
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

func (cc *MainChainContract) UpdatePKData(ctx CustomTransactionContextInterface, id string, newPayload string) error {
	GetWorldState(ctx)
	existing := ctx.GetData()

	if existing == nil {
		return fmt.Errorf("Cannot update public key in world state as key %s does not exist", id)
	}

	pk := new(PKData)
    pk.Payload = newPayload

	pkBytes, _ := json.Marshal(pk)

	err := ctx.GetStub().PutState(id, []byte(pkBytes))

	if err != nil {
		return errors.New("Unable to interact with world state")
	}

	return nil
}

func (cc *MainChainContract) NewIoTData(ctx CustomTransactionContextInterface, id string,  from string, payload string) error {
	GetWorldState(ctx)
	existing := ctx.GetData()

	if existing != nil {
		return fmt.Errorf("Cannot create new data in world state as key %s already exists", id)
	}

	data := new(CompressedData)
	data.From = from
	data.Payload = payload

	dataBytes, _ := json.Marshal(data)

	err := ctx.GetStub().PutState(id, []byte(dataBytes))

	if err != nil {
		return errors.New("Unable to interact with world state")
	}

	return nil
}

func (cc *MainChainContract) GetPKData(ctx CustomTransactionContextInterface, id string) (*PKData, error) {
	GetWorldState(ctx)
	existing := ctx.GetData()

	if existing == nil {
		return nil, fmt.Errorf("Cannot read world state pair with key %s. Does not exist", id)
	}

	data:= new(PKData)

	err := json.Unmarshal(existing, data)

	if err != nil {
		return nil, fmt.Errorf("Data retrieved from world state for key %s was not of type IoTData", id)
	}

	return data, nil
}

func (cc *MainChainContract) GetAllPKData(ctx CustomTransactionContextInterface) ([]*PKData, error) {
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

func (cc *MainChainContract) GetIoTData(ctx CustomTransactionContextInterface, id string) (*CompressedData, error) {
	GetWorldState(ctx)
	existing := ctx.GetData()

	if existing == nil {
		return nil, fmt.Errorf("Cannot read world state pair with key %s. Does not exist", id)
	}

	data:= new(CompressedData)

	err := json.Unmarshal(existing, data)

	if err != nil {
		return nil, fmt.Errorf("Data retrieved from world state for key %s was not of type IoTData", id)
	}

	return data, nil
}

func (cc *MainChainContract) DeleteData(ctx CustomTransactionContextInterface, id string) error {
	GetWorldState(ctx)
	existing := ctx.GetData()

	if existing == nil {
		return fmt.Errorf("Cannot read world state pair with key %s. Does not exist", id)
	}

	return ctx.GetStub().DelState(id)
}

// GetEvaluateTransactions returns functions of MainChainContract not to be tagged as submit
func (cc *MainChainContract) GetEvaluateTransactions() []string {
	return []string{"GetPKData","GetIoTData", "GetAllPKData"}
}